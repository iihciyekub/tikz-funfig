from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import load_json
from .recipes import load_recipe


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _unique_ids(items: Any, name: str, errors: list[str]) -> set[str]:
    if items is None:
        return set()
    if not isinstance(items, list):
        errors.append(f"{name} must be an array")
        return set()
    result: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{name}[{index}] must be an object")
            continue
        value = item.get("id")
        if not isinstance(value, str) or not value:
            errors.append(f"{name}[{index}].id is required")
            continue
        if value in result:
            errors.append(f"duplicate {name} id: {value}")
        result.add(value)
    return result


def validate_spec(spec: dict[str, Any], spec_path: Path | None = None) -> ValidationResult:
    errors: list[str] = []

    for field in ("schema_version", "id", "recipe", "kind"):
        if field not in spec:
            errors.append(f"missing required field: {field}")

    if spec.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    figure_id = spec.get("id")
    if not isinstance(figure_id, str) or not ID_RE.match(figure_id):
        errors.append("id must match ^[A-Za-z0-9][A-Za-z0-9._-]*$")

    kind = spec.get("kind")
    if kind not in {"pgfplots", "tikz"}:
        errors.append("kind must be 'pgfplots' or 'tikz'")

    recipe: dict[str, Any] | None = None
    recipe_id = spec.get("recipe")
    if isinstance(recipe_id, str):
        try:
            recipe = load_recipe(recipe_id)
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))
    else:
        errors.append("recipe must be a string")

    if recipe is not None:
        if recipe.get("kind") != kind:
            errors.append(
                f"recipe {recipe_id!r} requires kind={recipe.get('kind')!r}, got {kind!r}"
            )
        for field in recipe.get("required", []):
            if field not in spec:
                errors.append(f"recipe {recipe_id!r} requires field: {field}")

    axes = spec.get("axes")
    if isinstance(axes, dict):
        preset = axes.get("preset")
        if preset is not None and preset not in {"publication-offset", "standard"}:
            errors.append("axes.preset must be 'publication-offset' or 'standard'")

    source_ids = _unique_ids(spec.get("data_sources", []), "data_sources", errors)
    series_ids = _unique_ids(spec.get("series", []), "series", errors)

    source_types = {"function", "file", "coordinates", "gnuplot", "raw_gnuplot", "implicit"}
    for index, source in enumerate(spec.get("data_sources", [])):
        if not isinstance(source, dict):
            continue
        source_type = source.get("type")
        if source_type not in source_types:
            errors.append(f"data_sources[{index}].type is invalid: {source_type!r}")
            continue
        if source_type in {"function", "gnuplot"} and not source.get("expression"):
            errors.append(f"data_sources[{index}] type={source_type} requires expression")
        if source_type == "raw_gnuplot" and not source.get("script"):
            errors.append(f"data_sources[{index}] type=raw_gnuplot requires script")
        if source_type == "implicit" and not (source.get("expression") or source.get("equation")):
            errors.append(
                f"data_sources[{index}] type=implicit requires expression or equation"
            )
        if source_type == "file":
            path = source.get("path")
            if not isinstance(path, str) or not path:
                errors.append(f"data_sources[{index}] type=file requires path")
            elif spec_path is not None and not (spec_path.parent / path).exists():
                errors.append(f"data source file does not exist: {path}")
        if source_type == "coordinates" and not isinstance(source.get("points"), list):
            errors.append(f"data_sources[{index}] type=coordinates requires points")

    name_paths: set[str] = set()
    for index, series in enumerate(spec.get("series", [])):
        if not isinstance(series, dict):
            continue
        source_id = series.get("source")
        if source_id not in source_ids:
            errors.append(f"series[{index}] references unknown source: {source_id!r}")
        name_path = series.get("name_path")
        if isinstance(name_path, str):
            if name_path in name_paths:
                errors.append(f"duplicate series name_path: {name_path}")
            name_paths.add(name_path)

        plot = series.get("plot")
        if isinstance(plot, dict):
            plot_kind = plot.get("kind")
            if plot_kind == "quiver" and not (plot.get("u") and plot.get("v")):
                errors.append(f"series[{index}].plot kind=quiver requires u and v expressions")
            if plot_kind == "contour" and not plot.get("levels"):
                errors.append(f"series[{index}].plot kind=contour requires levels")
            if plot_kind == "heatmap":
                source = next(
                    (item for item in spec.get("data_sources", []) if item.get("id") == source_id),
                    None,
                )
                if source and source.get("type") == "coordinates":
                    bad = [point for point in source.get("points", []) if len(point) != 3]
                    if bad:
                        errors.append(
                            f"series[{index}].plot kind=heatmap requires coordinate points [x,y,meta]"
                        )

        scatter = series.get("scatter")
        if scatter is not None and not isinstance(scatter, dict):
            errors.append(f"series[{index}].scatter must be an object")

        error_bars = series.get("error_bars")
        if error_bars is not None:
            if not isinstance(error_bars, dict):
                errors.append(f"series[{index}].error_bars must be an object")
            else:
                for axis in ("x", "y"):
                    config = error_bars.get(axis)
                    if not config:
                        continue
                    mode = config.get("mode")
                    if mode in {"fixed", "fixed_relative"} and config.get("value") is None:
                        errors.append(
                            f"series[{index}].error_bars.{axis} mode={mode} requires value"
                        )
                    if mode in {"explicit", "explicit_relative"} and not any(
                        config.get(field) for field in ("column", "plus", "minus", "expr")
                    ):
                        errors.append(
                            f"series[{index}].error_bars.{axis} mode={mode} requires a column/plus/minus/expr binding"
                        )

    for index, region in enumerate(spec.get("regions", [])):
        if not isinstance(region, dict):
            continue
        if region.get("type") == "between":
            for field in ("path_a", "path_b"):
                path_name = region.get(field)
                if path_name not in name_paths:
                    errors.append(
                        f"regions[{index}].{field} references unknown name_path: {path_name!r}"
                    )

    for index, panel in enumerate(spec.get("panels", [])):
        if not isinstance(panel, dict):
            continue
        for series_id in panel.get("series", []):
            if series_id not in series_ids:
                errors.append(f"panels[{index}] references unknown series: {series_id!r}")

    for index, annotation in enumerate(spec.get("annotations", [])):
        if not isinstance(annotation, dict):
            continue
        annotation_type = annotation.get("type")
        if "label_style" in annotation:
            if not isinstance(annotation["label_style"], dict):
                errors.append(f"annotations[{index}].label_style must be an object")
            if annotation_type not in {"point", "intersection"}:
                errors.append(
                    f"annotations[{index}].label_style is only supported for point/intersection labels"
                )
        if annotation_type == "intersection":
            for field in ("path_a", "path_b"):
                path_name = annotation.get(field)
                if path_name not in name_paths:
                    errors.append(
                        f"annotations[{index}].{field} references unknown name_path: {path_name!r}"
                    )
            names = annotation.get("names")
            if names is not None:
                if not isinstance(names, list) or not names or not all(
                    isinstance(name, str) and name for name in names
                ):
                    errors.append(
                        f"annotations[{index}].names must be a non-empty array of coordinate names"
                    )
                elif len(set(names)) != len(names):
                    errors.append(f"annotations[{index}].names must be unique")
                labels = annotation.get("labels")
                if isinstance(labels, list) and len(labels) > len(names):
                    errors.append(
                        f"annotations[{index}].labels cannot contain more entries than names"
                    )
        if annotation_type in {"curve_probe", "curve_label"}:
            series_id = annotation.get("series")
            if series_id not in series_ids:
                errors.append(
                    f"annotations[{index}].series references unknown series: {series_id!r}"
                )
            position = annotation.get("position")
            if not isinstance(position, (int, float)) or not 0 <= position <= 1:
                errors.append(
                    f"annotations[{index}].position must be a number between 0 and 1"
                )
        if annotation_type == "coordinate_ref" and not annotation.get("ref"):
            errors.append(f"annotations[{index}] type=coordinate_ref requires ref")
        if annotation_type == "spy":
            for field in ("at", "in"):
                value = annotation.get(field)
                if not isinstance(value, list) or len(value) != 2:
                    errors.append(
                        f"annotations[{index}] type=spy requires {field}=[x,y]"
                    )
            magnification = annotation.get("magnification")
            if magnification is not None and (
                not isinstance(magnification, (int, float)) or magnification <= 0
            ):
                errors.append(
                    f"annotations[{index}].magnification must be a positive number"
                )

    diagram = spec.get("diagram")
    if diagram is not None:
        if not isinstance(diagram, dict):
            errors.append("diagram must be an object")
        else:
            node_ids = _unique_ids(diagram.get("nodes", []), "diagram.nodes", errors)
            for index, edge in enumerate(diagram.get("edges", [])):
                if not isinstance(edge, dict):
                    errors.append(f"diagram.edges[{index}] must be an object")
                    continue
                for field in ("from", "to"):
                    if edge.get(field) not in node_ids:
                        errors.append(
                            f"diagram.edges[{index}].{field} references unknown node: {edge.get(field)!r}"
                        )

    outputs = spec.get("outputs", {})
    if outputs is not None and not isinstance(outputs, dict):
        errors.append("outputs must be an object")
    elif isinstance(outputs, dict):
        basename = outputs.get("basename", "figure")
        if not isinstance(basename, str) or not ID_RE.match(basename):
            errors.append("outputs.basename must be a safe file basename")

    return ValidationResult(tuple(errors))


def load_and_validate(path: str | Path) -> tuple[dict[str, Any], ValidationResult]:
    spec_path = Path(path).resolve()
    spec = load_json(spec_path)
    return spec, validate_spec(spec, spec_path)
