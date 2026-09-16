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


def migrate_legacy_tex(
    source: str | Path,
    target_dir: str | Path,
    recipe: str | None = None,
) -> MigrationResult:
    source_path = Path(source).resolve()
    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    text = source_path.read_text(encoding="utf-8")

    has_rectangles = bool(RECTANGLE_RE.search(text))
    has_intersections = "name intersections" in text
    selected_recipe = recipe or (
        "publication-threshold" if has_rectangles or has_intersections else "data-series"
    )

    data_sources: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    detected = {
        "table_series": 0,
        "coordinate_series": 0,
        "regions": 0,
        "name_paths": 0,
    }
    counter = 0

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

    warnings: list[str] = []
    if "\\node" in text or "\\coordinate" in text:
        warnings.append(
            "manual TikZ nodes/coordinates were detected; review and recreate semantic callouts in annotations"
        )
    if "\\legend" in text:
        warnings.append("legacy legend content was detected; labels were not inferred automatically")
    if "name intersections" in text:
        warnings.append(
            "legacy intersections were detected; verify path pairs and add explicit intersection annotations"
        )
    if not series:
        warnings.append(
            "no supported addplot table/coordinates series were detected; migration scaffold is incomplete"
        )

    spec: dict[str, Any] = {
        "schema_version": "1.0",
        "id": source_path.stem.replace(" ", "-") + "-migrated",
        "recipe": selected_recipe,
        "kind": "pgfplots",
        "canvas": {"width": "10cm", "height": "7cm", "border": "2pt"},
        "engine": {"latex": "auto", "compute": "none"},
        "axes": _axis_spec(text),
        "data_sources": data_sources,
        "series": series,
        "regions": regions,
        "annotations": [],
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
