"""Measured TikZ geometry and conservative, object-addressable clearance checks."""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

PT_MM = 25.4 / 72.27
SAMPLES = 16


def length_mm(value: Any, default: float = 0.0) -> float:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)(pt|mm|cm|in|em|ex)\s*", str(value or ""))
    if not match:
        return default
    return float(match[1]) * {"pt": PT_MM, "mm": 1, "cm": 10, "in": 25.4,
                             "em": 3.2, "ex": 1.6}[match[2]]


MEASUREMENT_PREAMBLE = r"""
\newwrite\funfiggeometry
\immediate\openout\funfiggeometry=\jobname.ffgeom
\newdimen\funfigwest \newdimen\funfigeast
\newdimen\funfignorth \newdimen\funfigsouth
\newcommand{\funfigrecord}[3]{%
  \pgfextractx{\funfigwest}{\pgfpointanchor{#3}{west}}%
  \pgfextractx{\funfigeast}{\pgfpointanchor{#3}{east}}%
  \pgfextracty{\funfignorth}{\pgfpointanchor{#3}{north}}%
  \pgfextracty{\funfigsouth}{\pgfpointanchor{#3}{south}}%
  \immediate\write\funfiggeometry{#1|#2|\the\funfigwest|\the\funfigeast|\the\funfigsouth|\the\funfignorth}%
}
""".strip()


def records_tex(diagram: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for index, node in enumerate(diagram.get("nodes", [])):
        lines.append(r"\funfigrecord{node}{%d}{%s}" % (index, node["id"]))
    for index, group in enumerate(diagram.get("groups", [])):
        lines.append(r"\funfigrecord{group}{%d}{%s}" % (index, group["id"]))
        if group.get("label"):
            lines.append(r"\funfigrecord{group-label}{%d}{funfig_group_label_%d}" % (index, index))
    for index, edge in enumerate(diagram.get("edges", [])):
        if edge.get("label"):
            lines.append(r"\funfigrecord{edge-label}{%d}{funfig_edge_label_%d}" % (index, index))
        for sample in range(SAMPLES + 1):
            lines.append(r"\funfigrecord{point}{%d-%d}{funfig_path_%d_%d}" % (index, sample, index, sample))
    lines.append(r"\immediate\closeout\funfiggeometry")
    return lines


def read_geometry(path: Path, diagram: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"source": "tex-anchors", "units": "mm", "path_samples": SAMPLES,
                              "nodes": {}, "groups": {}, "labels": {}, "paths": {}}
    if not path.is_file():
        raise ValueError(f"missing TeX measurement output: {path}")
    points: dict[int, dict[int, list[float]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("|")
        if len(parts) != 6:
            raise ValueError(f"invalid geometry record: {line!r}")
        kind, key = parts[:2]
        vals = [float(v.removesuffix("pt")) * PT_MM for v in parts[2:]]
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("non-finite TeX geometry")
        west, east, south, north = vals
        box = {"x": (west + east) / 2, "y": (south + north) / 2,
               "width": east - west, "height": north - south,
               "left": west, "right": east, "bottom": south, "top": north}
        if kind == "point":
            edge_index, sample = map(int, key.split("-"))
            points.setdefault(edge_index, {})[sample] = [box["x"], box["y"]]
        else:
            index = int(key)
            family = "nodes" if kind == "node" else "groups" if kind.startswith("group") else "edges"
            item = diagram.get(family, [])[index]
            item_id = item.get("id", f"edge-{index}")
            destination = "labels" if kind.endswith("label") else family
            if destination == "labels":
                item_id = f"{kind}:{item_id}"
            result[destination][item_id] = box
    for index, samples in points.items():
        edge = diagram["edges"][index]
        if len(samples) != SAMPLES + 1:
            raise ValueError("incomplete path measurements")
        result["paths"][edge.get("id", f"edge-{index}")] = [samples[i] for i in range(SAMPLES + 1)]
        if edge.get('route') == 'polyline':
            # Exact corners prevent a sampled chord from cutting through an
            # obstacle which the actual orthogonal route goes around.
            result['paths'][edge.get('id', f'edge-{index}')] = [samples[0]] + [
                [p['x'] * 10, p['y'] * 10] for p in edge['routing']['points']] + [samples[SAMPLES]]
    if len(result["nodes"]) != len(diagram.get("nodes", [])):
        raise ValueError("incomplete node measurements")
    return result


def overlap(a: dict[str, float], b: dict[str, float], tolerance: float = 0.15) -> bool:
    return (min(a["right"], b["right"]) - max(a["left"], b["left"]) > tolerance
            and min(a["top"], b["top"]) - max(a["bottom"], b["bottom"]) > tolerance)


def segment_hits(a: list[float], b: list[float], box: dict[str, float], margin: float = 0.0) -> bool:
    # Liang–Barsky: includes vertical/horizontal paths and boundary clearance.
    low, high = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - box["left"] + margin), (dx, box["right"] + margin - a[0]),
                 (-dy, a[1] - box["bottom"] + margin), (dy, box["top"] + margin - a[1])):
        if abs(p) < 1e-10:
            if q < 0:
                return False
        elif p < 0:
            low = max(low, q / p)
        else:
            high = min(high, q / p)
        if low > high:
            return False
    return True


def geometry_defects(diagram: dict[str, Any], geometry: dict[str, Any]) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = []
    nodes, labels = geometry.get("nodes", {}), geometry.get("labels", {})
    def add(kind: str, ids: list[str], **evidence: Any) -> None:
        defects.append({"id": kind + ":" + ":".join(ids), "type": kind, "objects": ids,
                        "severity": "error", "evidence": evidence})
    pairs = list(nodes.items())
    for i, (left, a) in enumerate(pairs):
        for right, b in pairs[i + 1:]:
            if overlap(a, b):
                add("node-overlap", [left, right])
    for label, box in labels.items():
        for node, nbox in nodes.items():
            if overlap(box, nbox):
                add("label-node-overlap", [label, node])
    lpairs = list(labels.items())
    for i, (left, a) in enumerate(lpairs):
        for right, b in lpairs[i + 1:]:
            if overlap(a, b):
                add("label-overlap", [left, right])
    for index, edge in enumerate(diagram.get("edges", [])):
        eid = edge.get("id", f"edge-{index}")
        path = geometry.get("paths", {}).get(eid, [])
        for node, box in nodes.items():
            if node in {edge["from"], edge.get("to")}:
                continue
            if any(segment_hits(a, b, box) for a, b in zip(path, path[1:])):
                add("edge-node-crossing", [eid, node], sampled=True)
        for label, box in labels.items():
            if label == f"edge-label:{eid}":
                continue  # a path's own label intentionally sits on that path
            if any(segment_hits(a, b, box) for a, b in zip(path, path[1:])):
                add("edge-label-crossing", [eid, label], sampled=True)
    groups = {g["id"]: g for g in diagram.get("groups", [])}
    def descendants(gid: str) -> set[str]:
        result: set[str] = set()
        for member in groups[gid]["members"]:
            result.add(member)
            if member in groups:
                result.update(descendants(member))
        return result
    for gid, box in geometry.get("groups", {}).items():
        members = descendants(gid)
        for nid, nbox in nodes.items():
            if nid not in members and overlap(box, nbox):
                add("group-node-overlap", [gid, nid])
        for member in members:
            mbox = nodes.get(member) or geometry.get("groups", {}).get(member)
            if mbox and any((mbox["left"] < box["left"] - .15, mbox["right"] > box["right"] + .15,
                             mbox["bottom"] < box["bottom"] - .15, mbox["top"] > box["top"] + .15)):
                add("group-containment", [gid, member])
        for other, obox in geometry.get('groups', {}).items():
            if gid < other and other not in members and gid not in descendants(other) and overlap(box, obox):
                add('group-overlap', [gid, other])
    return defects
