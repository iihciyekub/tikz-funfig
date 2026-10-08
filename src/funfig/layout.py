"""Deterministic, semantics-preserving composition and executable constraints."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

from .geometry import length_mm
from .theme import load_profile

CONSTRAINTS = {"align-x", "align-y", "equal-width", "equal-height", "order-x", "order-y", "pin"}


def semantic_signature(spec: dict[str, Any]) -> str:
    diagram = spec.get("diagram", {})
    payload = {"recipe": spec.get("recipe"), "nodes": [], "edges": [], "groups": []}
    for family, fields in (("nodes", ("id", "label", "label_format", "role", "shape")),
                           ("edges", ("id", "from", "to", "to_edge", "arrows", "label", "label_format")),
                           ("groups", ("id", "members", "label", "label_format"))):
        payload[family] = sorted([{k: item[k] for k in fields if k in item}
                                  for item in diagram.get(family, [])], key=lambda x: json.dumps(x, sort_keys=True))
    # Include data/units/axes for future mixed compositions; visual optimization
    # never becomes permission to change scientific values.
    for field in ("data_sources", "series", "axes", "petri"):
        if field in spec:
            payload[field] = spec[field]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def profile_for(spec: dict[str, Any]) -> dict[str, Any]:
    profile = load_profile((spec.get("profile") or {}).get("id", "journal-single-column"))
    layout = (spec.get("diagram") or {}).get("layout") or {}
    for field in ("target_width_mm", "minimum_text_pt"):
        if field in layout:
            profile[field] = layout[field]
    return profile


def validate_constraints(layout: dict[str, Any], node_ids: set[str]) -> list[str]:
    errors: list[str] = []
    records = layout.get("constraints", [])
    if not isinstance(records, list):
        return ["diagram.layout.constraints must be an array"]
    for i, record in enumerate(records):
        prefix = f"diagram.layout.constraints[{i}]"
        if not isinstance(record, dict) or record.get("type") not in CONSTRAINTS:
            errors.append(prefix + " has an unsupported type")
            continue
        ids = record.get("nodes")
        if not isinstance(ids, list) or not ids or any(not isinstance(n, str) or n not in node_ids for n in ids):
            errors.append(prefix + " requires existing node IDs")
            continue
        if len(ids) != len(set(ids)):
            errors.append(prefix + " contains duplicate node IDs")
        if record["type"] != "pin" and len(ids) < 2:
            errors.append(prefix + " requires at least two nodes")
        if record["type"] == "pin" and (len(ids) != 1 or any(
            isinstance(record.get(k), bool) or not isinstance(record.get(k), (float, int))
            or not math.isfinite(record[k]) for k in ("x", "y"))):
            errors.append(prefix + " pin requires one node and finite x/y in cm")
        if set(record) - {"type", "nodes", "x", "y", "gap"}:
            errors.append(prefix + " contains unknown fields")
        if record['type'] != 'pin' and any(k in record for k in ('x', 'y')):
            errors.append(prefix + ' x/y apply only to pin constraints')
        if 'gap' in record and record['type'] not in {'order-x', 'order-y'}:
            errors.append(prefix + ' gap applies only to ordering constraints')
        if record.get("gap") is not None and length_mm(record["gap"], -1) <= 0:
            errors.append(prefix + " gap must be a positive TeX length")
    return errors


def estimate_dimensions(node: dict[str, Any], profile: dict[str, Any], text_width: float = 32) -> tuple[float, float]:
    width = length_mm(node.get("text_width"), text_width)
    label = str(node.get("label", ""))
    visual = sum(1 if ord(c) > 0x2E7F else .56 for c in label)
    lines = max(1, math.ceil(visual / max(width / 3.2, 1)), label.count("\\\\") + 1)
    w = max(length_mm(node.get("min_width")), width + 2 * length_mm(profile.get("node_inner_xsep"), 2.1))
    h = max(length_mm(node.get("min_height")), length_mm(profile.get("node_min_height"), 8),
            lines * 3.9 + 2 * length_mm(profile.get("node_inner_ysep"), 1.4))
    shape = node.get("shape", "diamond" if node.get("role") == "decision" else "rectangle")
    if shape == "diamond":
        w, h = w + 2 * h, h + w / 2
    elif shape == "circle":
        w = h = math.hypot(w, h)
    elif shape == "ellipse":
        w, h = w * 1.42, h * 1.42
    return w, h


def _layers(diagram: dict[str, Any]) -> dict[str, int]:
    """Stable topological ranks; DFS back edges are reserved for feedback lanes."""
    ids = [n['id'] for n in diagram.get('nodes', [])]
    outgoing = {n: [] for n in ids}
    for edge in diagram.get('edges', []):
        if edge.get('to') in outgoing and edge['from'] != edge['to']:
            outgoing[edge['from']].append(edge['to'])
    state = {}; dag = {n: [] for n in ids}
    def visit(n):
        state[n] = 1
        for target in outgoing[n]:
            if state.get(target) == 1:
                continue
            dag[n].append(target)
            if not state.get(target):
                visit(target)
        state[n] = 2
    for n in ids:
        if not state.get(n):
            visit(n)
    indegree = {n: 0 for n in ids}
    for targets in dag.values():
        for n in targets:
            indegree[n] += 1
    queue = [n for n in ids if not indegree[n]]
    rank = {n: 0 for n in ids}
    for n in queue:
        for target in dag[n]:
            rank[target] = max(rank[target], rank[n] + 1)
            indegree[target] -= 1
            if not indegree[target]:
                queue.append(target)
    return rank


def apply_constraints(spec: dict[str, Any], dimensions: dict[str, tuple[float, float]]) -> list[dict[str, Any]]:
    diagram = spec["diagram"]
    constraints = diagram.get("layout", {}).get("constraints", [])
    nodes = {n["id"]: n for n in diagram["nodes"]}
    pins = {c["nodes"][0]: (float(c["x"]) * 10, float(c["y"]) * 10)
            for c in constraints if c["type"] == "pin"}
    positions = {n: [v["position"]["x"] * 10, v["position"]["y"] * 10] for n, v in nodes.items()}
    for n, p in pins.items():
        positions[n] = list(p)
    for _ in range(max(2, len(constraints) * 2)):
        for c in constraints:
            typ, ids = c["type"], c["nodes"]
            if typ.startswith("equal-"):
                axis = 0 if typ == "equal-width" else 1
                size = max(dimensions[n][axis] for n in ids)
                for n in ids:
                    node = nodes[n]
                    node["min_width" if axis == 0 else "min_height"] = f"{size:.3f}mm"
                    dimensions[n] = tuple(size if k == axis else v for k, v in enumerate(dimensions[n]))
            elif typ.startswith("align-"):
                axis = 0 if typ == "align-x" else 1
                locked = [pins[n][axis] for n in ids if n in pins]
                target = locked[0] if locked else sum(positions[n][axis] for n in ids) / len(ids)
                for n in ids:
                    if n not in pins:
                        positions[n][axis] = target
            elif typ.startswith("order-"):
                axis = 0 if typ == "order-x" else 1
                sign = 1 if axis == 0 else -1  # reading order is left-right / top-bottom
                for a, b in zip(ids, ids[1:]):
                    gap = length_mm(c.get("gap"), 6) + (dimensions[a][axis] + dimensions[b][axis]) / 2
                    deficit = gap - sign * (positions[b][axis] - positions[a][axis])
                    if deficit > 0:
                        if b not in pins:
                            positions[b][axis] += sign * deficit
                        elif a not in pins:
                            positions[a][axis] -= sign * deficit
    for n, pos in positions.items():
        nodes[n]["position"] = {"type": "absolute", "x": round(pos[0] / 10, 6), "y": round(pos[1] / 10, 6)}
    boxes = {n: {"x": p[0], "y": p[1], "width": dimensions[n][0], "height": dimensions[n][1]}
             for n, p in positions.items()}
    return constraint_defects(diagram, boxes)


def constraint_defects(diagram: dict[str, Any], boxes: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    defects = []
    for index, c in enumerate(diagram.get("layout", {}).get("constraints", [])):
        ids, typ = c["nodes"], c["type"]
        if any(n not in boxes for n in ids):
            bad = True
        elif typ.startswith("align-"):
            field = "x" if typ == "align-x" else "y"
            values = [boxes[n][field] for n in ids]
            bad = max(values) - min(values) > .2
        elif typ.startswith("equal-"):
            field = "width" if typ == "equal-width" else "height"
            values = [boxes[n][field] for n in ids]
            bad = max(values) - min(values) > .3
        elif typ == "pin":
            b = boxes[ids[0]]
            bad = abs(b["x"] - c["x"] * 10) > .2 or abs(b["y"] - c["y"] * 10) > .2
        else:
            axis, size, sign = ("x", "width", 1) if typ == "order-x" else ("y", "height", -1)
            gap = length_mm(c.get("gap"), 6)
            bad = any(sign * (boxes[b][axis] - boxes[a][axis]) <
                      (boxes[a][size] + boxes[b][size]) / 2 + gap - .2 for a, b in zip(ids, ids[1:]))
        if bad:
            defects.append({"id": f"constraint:{index}", "type": "constraint-conflict",
                            "objects": ids, "severity": "error", "evidence": {"constraint": c}})
    return defects


def plan_layout(spec: dict[str, Any], geometry: dict[str, Any] | None = None,
                *, direction: str | None = None, grid: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    planned = copy.deepcopy(spec)
    diagram = planned["diagram"]
    layout = diagram.setdefault("layout", {"type": "auto"})
    profile = profile_for(spec)
    target = float(profile["target_width_mm"])
    gap = length_mm(layout.get("clearance"), 6)
    direction = direction or layout.get("direction", "right")
    nodes = diagram.get("nodes", [])
    ranks = _layers(diagram)
    columns = (max(ranks.values(), default=0) + 1 if direction == "right" else
               max((list(ranks.values()).count(rank) for rank in set(ranks.values())), default=1))
    text_width = max(15, min(38, (target - 8 - gap * (columns - 1)) / columns - 4.2))
    measurements = (geometry or {}).get("nodes", {})
    dimensions: dict[str, tuple[float, float]] = {}
    cells: dict[str, tuple[int, int]] = {}
    lanes: dict[int, int] = {}
    for node in nodes:
        nid = node["id"]
        if not node.get("text_width"):
            node["text_width"] = f"{text_width:.3f}mm"
        measured = measurements.get(nid)
        dimensions[nid] = ((round(measured["width"], 3), round(measured["height"], 3)) if measured
                           else estimate_dimensions(node, profile, text_width))
        pos = node.get("position", {})
        if grid and pos.get("type") == "grid":
            cells[nid] = pos["column"], pos["row"]
        else:
            rank = ranks[nid]
            lane = lanes.get(rank, 0)
            lanes[rank] = lane + 1
            cells[nid] = (rank, lane) if direction == "right" else (lane, rank)
    # Dimension equality must affect track sizes before placement.
    for c in layout.get("constraints", []):
        if c["type"] in {"equal-width", "equal-height"}:
            axis = 0 if c["type"] == "equal-width" else 1
            size = max(dimensions[n][axis] for n in c["nodes"])
            for n in c["nodes"]:
                dimensions[n] = tuple(size if k == axis else v for k, v in enumerate(dimensions[n]))
    cols: dict[int, float] = {}
    rows: dict[int, float] = {}
    for nid, (column, row) in cells.items():
        cols[column] = max(cols.get(column, 0), dimensions[nid][0])
        rows[row] = max(rows.get(row, 0), dimensions[nid][1])
    # Group borders and headings are part of the space budget, not an afterthought.
    group_padding = max((length_mm(g.get("padding"), 2.1) for g in diagram.get("groups", [])), default=0)
    title_budget = max((length_mm(g.get("title_gap"), 6) for g in diagram.get("groups", []) if g.get("label")), default=0)
    horizontal_gap = max(gap, 2 * group_padding + 3)
    vertical_gap = max(gap, 2 * group_padding + title_budget + 3)
    def centers(tracks: dict[int, float], spacing: float, minimum_step: float) -> dict[int, float]:
        result: dict[int, float] = {}
        previous = None
        for i in sorted(tracks):
            result[i] = 0 if previous is None else result[previous] + max(minimum_step, (tracks[previous] + tracks[i]) / 2 + spacing)
            previous = i
        return result
    xs = centers(cols, horizontal_gap, length_mm(layout.get('column_gap')) if grid else 0)
    ys = centers(rows, vertical_gap, length_mm(layout.get('row_gap')) if grid else 0)
    for node in nodes:
        col, row = cells[node["id"]]
        node["position"] = {"type": "absolute", "x": round(xs[col] / 10, 4), "y": round(-ys[row] / 10, 4)}
    layout["type"] = "manual"
    layout["measure"] = True
    conflicts = apply_constraints(planned, dimensions)
    width = max((n["position"]["x"] * 10 + dimensions[n["id"]][0] / 2 for n in nodes), default=0) - min(
        (n["position"]["x"] * 10 - dimensions[n["id"]][0] / 2 for n in nodes), default=0)
    if width + 2 * group_padding + 2 > target:
        conflicts.append({"id": "width-budget", "type": "space-infeasible", "severity": "error",
                          "objects": [n["id"] for n in nodes], "evidence": {
                              "required_width_mm": round(width + 2 * group_padding + 2, 2),
                              "target_width_mm": target, "alternatives": ["down", "grouped", "panels"]}})
    assert semantic_signature(planned) == semantic_signature(spec)
    return planned, {"direction": direction, "dimensions": dimensions, "conflicts": conflicts,
                     "measurement": "tex-anchors" if geometry else "estimate", "semantic_signature": semantic_signature(spec)}
