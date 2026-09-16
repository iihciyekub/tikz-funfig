from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import write_json_atomic
from .schema import validate_spec


AXIS_NUMBER_RE = {
    key: re.compile(rf"\b{key}\s*=\s*(-?\d+(?:\.\d+)?)")
    for key in ("xmin", "xmax", "ymin", "ymax")
}
TICKS_RE = {
    key: re.compile(rf"\b{key}\s*=\s*\{{([^}}]+)\}}")
    for key in ("xtick", "ytick")
}
ADDPLOT_RE = re.compile(r"\\addplot\+?\s*(.*?);", re.DOTALL)
LEADING_OPTIONS_RE = re.compile(r"^\s*\[(.*?)\]\s*(.*)$", re.DOTALL)
TABLE_BODY_RE = re.compile(r"^table(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}\s*$", re.DOTALL)
COORD_BODY_RE = re.compile(r"^coordinates\s*\{([^}]+)\}\s*$", re.DOTALL)
POINT_RE = re.compile(r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)")
RECTANGLE_RE = re.compile(
    r"\\fill\s*(?:\[(.*?)\])?\s*\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)\s*rectangle\s*\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)\s*;",
    re.DOTALL,
)
NAME_PATH_RE = re.compile(r"name\s+path\s*=\s*([A-Za-z0-9._-]+)")
LEGACY_METHOD_START_RE = re.compile(r"(?m)^[ \t]*\\(?P<name>iiplot|iipolt)\b")
ADDSYMBOL_RE = re.compile(r"\\addsymbol\{([^{}]+)\}\{([^{}]*)\}")
ADDPOINT_RE = re.compile(r"\\addpoint\{([^{}]+)\}\{([^{}]+)\}")
TAIL_NODE_RE = re.compile(
    r"node\s*\[[^\]]*\bpos\s*=\s*([0-9.]+)[^\]]*\]\s*\{([^{}]*)\}",
    re.DOTALL,
)
SINGLE_SPLOT_RE = re.compile(
    r"\bsplot\s*(?:\[([^\]]+)\])?\s*(?:\[([^\]]+)\])?\s*([^;]+?)(?:;|$)",
    re.DOTALL,
)
SIMPLE_INTERSECTION_RE = re.compile(
    r"name\s+intersections\s*=\s*\{\s*of\s*=\s*([A-Za-z0-9._-]+)\s+and\s+"
    r"([A-Za-z0-9._-]+)\s*,\s*by\s*=\s*\{?([A-Za-z0-9._,-]+)\}?\s*\}",
    re.DOTALL,
)
CALXY_RE = re.compile(r"\\calxy(?:\[(x|y|xy)\])?\{([A-Za-z0-9._-]+)\}")


@dataclass(frozen=True)
class MigrationResult:
    spec_path: Path
    warnings: tuple[str, ...]
    detected: dict[str, int]


def _numbers(raw: str) -> list[float]:
    result: list[float] = []
    for token in raw.split(","):
        token = token.strip()
        try:
            result.append(float(token))
        except ValueError:
            continue
    return result


def _axis_spec(text: str) -> dict[str, Any]:
    axes: dict[str, Any] = {
        "x": {},
        "y": {},
        "grid": "major" if re.search(r"\bgrid\s*=\s*major\b", text) else "none",
    }
    for key, pattern in AXIS_NUMBER_RE.items():
        match = pattern.search(text)
        if match:
            axis = key[0]
            bound = "min" if key.endswith("min") else "max"
            axes[axis][bound] = float(match.group(1))
    for key, pattern in TICKS_RE.items():
        match = pattern.search(text)
        if match:
            axes[key[0]]["ticks"] = _numbers(match.group(1))
    return axes


def _relative_data_path(source_tex: Path, target_dir: Path, raw_path: str) -> str:
    candidate = (source_tex.parent / raw_path.strip()).resolve()
    return os.path.relpath(candidate, target_dir.resolve())


def _name_path(options: str | None) -> str | None:
    if not options:
        return None
    match = NAME_PATH_RE.search(options)
    return match.group(1) if match else None


def _split_addplot(statement: str) -> tuple[str, str]:
    match = LEADING_OPTIONS_RE.match(statement)
    if not match:
        return "", statement.strip()
    return match.group(1).strip(), match.group(2).strip()


def _skip_space(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _balanced_group(
    text: str, index: int, opener: str, closer: str
) -> tuple[str, int] | None:
    if index >= len(text) or text[index] != opener:
        return None
    depth = 0
    cursor = index
    while cursor < len(text):
        char = text[cursor]
        if char == opener and (cursor == 0 or text[cursor - 1] != "\\"):
            depth += 1
        elif char == closer and (cursor == 0 or text[cursor - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[index + 1 : cursor], cursor + 1
        cursor += 1
    return None


def _legacy_method_calls(text: str) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for match in LEGACY_METHOD_START_RE.finditer(text):
        cursor = _skip_space(text, match.end())
        optionals: list[str] = []
        while cursor < len(text) and text[cursor] == "[":
            parsed = _balanced_group(text, cursor, "[", "]")
            if parsed is None:
                break
            value, cursor = parsed
            optionals.append(value.strip())
            cursor = _skip_space(text, cursor)
        parsed_body = _balanced_group(text, cursor, "{", "}")
        if parsed_body is None:
            continue
        body, cursor = parsed_body
        tail_end = text.find(";", cursor)
        if tail_end == -1 or tail_end - cursor > 600:
            tail_end = cursor
        tail = text[cursor:tail_end]
        calls.append(
            {
                "macro": match.group("name"),
                "optionals": optionals,
                "body": body,
                "tail": tail,
            }
        )
    return calls


def _float_or_none(value: str) -> float | None:
    try:
        return float(value.strip())
    except ValueError:
        return None


def _safe_figure_id(stem: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-._")
    return (value or "legacy-figure") + "-migrated"


def _legacy_method_source(
    call: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    body = re.sub(r"(?m)%.*$", "", call["body"]).strip()
    warnings: list[str] = []
    splots = list(SINGLE_SPLOT_RE.finditer(body))
    if len(splots) == 0:
        if re.search(r"\bplot\b", body) and "\\" not in body:
            option = (call.get("optionals") or [""])[0]
            option_parts = [part.strip() for part in option.split(",") if part.strip()]
            path_name = option_parts[0] if option_parts else None
            return {"type": "raw_gnuplot", "script": body}, path_name, warnings
        warnings.append(
            f"legacy \\{call['macro']} contains no directly portable splot/plot statement; review manually"
        )
        return None, None, warnings
    if len(splots) != 1:
        warnings.append(
            f"legacy \\{call['macro']} contains {len(splots)} splot statements; review as raw gnuplot"
        )
        return None, None, warnings
    match = splots[0]
    expression = match.group(3).strip()
    if "\\" in expression or "," in expression:
        warnings.append(
            f"legacy \\{call['macro']} splot uses TeX macros/gnuplot assignments; manual review required"
        )
        return None, None, warnings
    source: dict[str, Any] = {
        "type": "implicit",
        "expression": expression,
        "level": 0,
        "samples": 100,
        "isosamples": 100,
    }
    if match.group(1):
        source["domain"] = match.group(1).strip()
    if match.group(2):
        source["y_domain"] = match.group(2).strip()

    option = (call.get("optionals") or [""])[0]
    option_parts = [part.strip() for part in option.split(",") if part.strip()]
    path_name = option_parts[0] if option_parts else None
    return source, path_name, warnings


def _legacy_tail_annotations(
    tail: str, series_id: str, warnings: list[str]
) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    for match in ADDPOINT_RE.finditer(tail):
        first = _float_or_none(match.group(1))
        second = _float_or_none(match.group(2))
        if first is None or second is None:
            warnings.append("legacy \\addpoint has non-numeric position/angle; review manually")
            continue
        if 0 <= first <= 1:
            position, angle = first, second
        elif 0 <= second <= 1:
            position, angle = second, first
            warnings.append("legacy \\addpoint argument order was reversed and normalized")
        else:
            warnings.append("legacy \\addpoint has no argument in [0,1]; review manually")
            continue
        annotations.append(
            {
                "type": "curve_probe",
                "series": series_id,
                "position": position,
                "show": "xy",
                "precision": 2,
                "pin_angle": angle,
            }
        )
    for match in ADDSYMBOL_RE.finditer(tail):
        position = _float_or_none(match.group(1))
        if position is None or not 0 <= position <= 1:
            warnings.append("legacy \\addsymbol position is invalid; review manually")
            continue
        annotations.append(
            {
                "type": "curve_label",
                "series": series_id,
                "position": position,
                "label": match.group(2),
                "sloped": True,
            }
        )
    node_match = TAIL_NODE_RE.search(tail)
    if node_match:
        position = _float_or_none(node_match.group(1))
        if position is not None and 0 <= position <= 1:
            annotations.append(
                {
                    "type": "curve_label",
                    "series": series_id,
                    "position": position,
                    "label": node_match.group(2),
                    "sloped": False,
                }
            )
    return annotations


def migrate_legacy_tex(
    source: str | Path,
    target_dir: str | Path,
    recipe: str | None = None,
) -> MigrationResult:
    source_path = Path(source).resolve()
    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    text = source_path.read_text(encoding="utf-8")
    legacy_method_calls = _legacy_method_calls(text)

    has_rectangles = bool(RECTANGLE_RE.search(text))
    has_intersections = "name intersections" in text
    selected_recipe = recipe or (
        "publication-threshold"
        if has_rectangles
        else (
            "implicit-function"
            if legacy_method_calls
            else ("intersection-curves" if has_intersections else "data-series")
        )
    )

    data_sources: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    detected = {
        "table_series": 0,
        "coordinate_series": 0,
        "implicit_series": 0,
        "gnuplot_series": 0,
        "regions": 0,
        "name_paths": 0,
        "method_annotations": 0,
        "intersections": 0,
        "coordinate_refs": 0,
    }
    counter = 0
    warnings: list[str] = []
    annotations: list[dict[str, Any]] = []

    for statement_match in ADDPLOT_RE.finditer(text):
        options, body = _split_addplot(statement_match.group(1))
        table_match = TABLE_BODY_RE.match(body)
        coord_match = COORD_BODY_RE.match(body)
        if table_match:
            counter += 1
            source_id = f"legacy-data-{counter}"
            data_sources.append(
                {
                    "id": source_id,
                    "type": "file",
                    "path": _relative_data_path(source_path, target, table_match.group(1)),
                }
            )
            detected["table_series"] += 1
        elif coord_match:
            points = [[float(x), float(y)] for x, y in POINT_RE.findall(coord_match.group(1))]
            if not points:
                continue
            counter += 1
            source_id = f"legacy-coordinates-{counter}"
            data_sources.append({"id": source_id, "type": "coordinates", "points": points})
            detected["coordinate_series"] += 1
        else:
            continue

        item: dict[str, Any] = {"id": f"legacy-series-{counter}", "source": source_id}
        name_path = _name_path(options)
        if name_path:
            item["name_path"] = name_path
            detected["name_paths"] += 1
        if options:
            cleaned = NAME_PATH_RE.sub("", options).strip(" ,")
            if cleaned:
                item["options"] = [cleaned]
        series.append(item)

    for method_index, call in enumerate(legacy_method_calls, start=1):
        source, path_name, method_warnings = _legacy_method_source(call)
        warnings.extend(method_warnings)
        if source is None:
            continue
        counter += 1
        source_id = f"legacy-method-{method_index}"
        source["id"] = source_id
        data_sources.append(source)
        series_id = f"legacy-series-{counter}"
        item: dict[str, Any] = {"id": series_id, "source": source_id}
        if path_name:
            item["name_path"] = path_name
            detected["name_paths"] += 1
        series.append(item)
        if source.get("type") == "implicit":
            detected["implicit_series"] += 1
        elif source.get("type") == "raw_gnuplot":
            detected["gnuplot_series"] += 1
        tail_annotations = _legacy_tail_annotations(call.get("tail", ""), series_id, warnings)
        annotations.extend(tail_annotations)
        detected["method_annotations"] += len(tail_annotations)

    regions: list[dict[str, Any]] = []
    for index, match in enumerate(RECTANGLE_RE.finditer(text), start=1):
        regions.append(
            {
                "id": f"legacy-region-{index}",
                "type": "rectangle",
                "x1": float(match.group(2)),
                "y1": float(match.group(3)),
                "x2": float(match.group(4)),
                "y2": float(match.group(5)),
                "style": {"fill": "gray!25", "fill_opacity": 0.3},
            }
        )
        detected["regions"] += 1

    intersection_refs: set[str] = set()
    available_paths = {
        item.get("name_path") for item in series if isinstance(item.get("name_path"), str)
    }
    active_text = re.sub(r"(?m)%.*$", "", text)
    for match in SIMPLE_INTERSECTION_RE.finditer(active_text):
        path_a, path_b = match.group(1), match.group(2)
        if path_a not in available_paths or path_b not in available_paths:
            warnings.append(
                f"legacy intersection {path_a!r}/{path_b!r} references paths not migrated; review manually"
            )
            continue
        names = [name.strip() for name in match.group(3).split(",") if name.strip()]
        if not names:
            continue
        annotation: dict[str, Any] = {
            "type": "intersection",
            "path_a": path_a,
            "path_b": path_b,
        }
        if len(names) == 1:
            annotation["name"] = names[0]
        else:
            annotation["names"] = names
        annotations.append(annotation)
        intersection_refs.update(names)
        detected["intersections"] += 1

    seen_coordinate_refs: set[tuple[str, str]] = set()
    for match in CALXY_RE.finditer(active_text):
        show = match.group(1) or "xy"
        ref = match.group(2)
        if ref not in intersection_refs:
            continue
        key = (ref, show)
        if key in seen_coordinate_refs:
            continue
        seen_coordinate_refs.add(key)
        annotations.append(
            {
                "type": "coordinate_ref",
                "ref": ref,
                "show": show,
                "precision": 2,
            }
        )
        detected["coordinate_refs"] += 1

    if "\\node" in text or "\\coordinate" in text:
        warnings.append(
            "manual TikZ nodes/coordinates were detected; review and recreate semantic callouts in annotations"
        )
    if "\\legend" in text:
        warnings.append("legacy legend content was detected; labels were not inferred automatically")
    if "name intersections" in text and not detected["intersections"]:
        warnings.append(
            "legacy intersections were detected; verify path pairs and add explicit intersection annotations"
        )
    if not series:
        warnings.append(
            "no supported plot series were detected; migration scaffold is incomplete"
        )

    spec: dict[str, Any] = {
        "schema_version": "1.0",
        "id": _safe_figure_id(source_path.stem),
        "recipe": selected_recipe,
        "kind": "pgfplots",
        "canvas": {"width": "10cm", "height": "7cm", "border": "2pt"},
        "engine": {
            "latex": "auto",
            "compute": (
                "gnuplot"
                if detected["implicit_series"] or detected["gnuplot_series"]
                else "none"
            ),
        },
        "axes": _axis_spec(text),
        "data_sources": data_sources,
        "series": series,
        "regions": regions,
        "annotations": annotations,
        "outputs": {"basename": "figure", "keep_build": False},
        "metadata": {
            "migration": {
                "status": "draft",
                "source": str(source_path),
                "warnings": warnings,
                "detected": detected,
            }
        },
    }
    spec_path = target / "figure.funfig.json"
    write_json_atomic(spec_path, spec)
    validation = validate_spec(spec, spec_path)
    if not validation.ok:
        raise ValueError(
            "generated migration draft is invalid:\n- " + "\n- ".join(validation.errors)
        )
    return MigrationResult(spec_path=spec_path, warnings=tuple(warnings), detected=detected)
