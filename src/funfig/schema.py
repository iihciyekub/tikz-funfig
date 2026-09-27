from __future__ import annotations

import re
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import load_json
from .recipes import load_recipe
from .theme import load_profile, load_theme


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
LENGTH_RE = re.compile(r"^\s*\d+(?:\.\d+)?(?:pt|mm|cm|in|em|ex)\s*$")
PETRI_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


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


def _has_cycle(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for target in graph.get(node, set()):
            if visit(target):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def _validate_length(value: Any, path: str, errors: list[str]) -> None:
    if value is not None and (not isinstance(value, str) or not LENGTH_RE.match(value)):
        errors.append(f"{path} must be a positive TeX length such as 12mm or 8pt")


def _validate_petri(petri: Any, errors: list[str]) -> None:
    if not isinstance(petri, dict):
        errors.append("petri must be an object")
        return
    allowed = {"places", "transitions", "arcs"}
    for key in set(petri) - allowed:
        errors.append(f"petri.{key} is not allowed")
    node_sets: dict[str, set[str]] = {}
    for family in ("places", "transitions"):
        nodes = petri.get(family)
        if not isinstance(nodes, list) or not nodes:
            errors.append(f"petri.{family} must be a non-empty array")
            nodes = []
        ids: set[str] = set()
        for index, node in enumerate(nodes):
            path = f"petri.{family}[{index}]"
            if not isinstance(node, dict):
                errors.append(f"{path} must be an object")
                continue
            allowed_node = {"id", "label", "label_format", "position"}
            if family == "places":
                allowed_node.add("tokens")
            for key in set(node) - allowed_node:
                errors.append(f"{path}.{key} is not allowed")
            node_id = node.get("id")
            if not isinstance(node_id, str) or not PETRI_ID_RE.fullmatch(node_id):
                errors.append(f"{path}.id must be a TikZ-safe identifier")
            elif node_id in ids:
                errors.append(f"duplicate petri.{family} id: {node_id}")
            else:
                ids.add(node_id)
            if not isinstance(node.get("label"), str):
                errors.append(f"{path}.label must be a string")
            if node.get("label_format", "plain") not in {"plain", "tex"}:
                errors.append(f"{path}.label_format must be plain or tex")
            position = node.get("position")
            if not isinstance(position, dict) or set(position) != {"x", "y"} or any(
                not isinstance(position[key], (int, float))
                or isinstance(position[key], bool)
                or not math.isfinite(position[key])
                for key in ("x", "y") if isinstance(position, dict) and key in position
            ):
                errors.append(f"{path}.position requires finite numeric x and y")
            if family == "places":
                tokens = node.get("tokens")
                if type(tokens) is not int or tokens < 0:
                    errors.append(f"{path}.tokens must be a non-negative integer")
        node_sets[family] = ids
    overlap = node_sets["places"] & node_sets["transitions"]
    if overlap:
        errors.append("Petri place and transition IDs must be disjoint: " + ", ".join(sorted(overlap)))
    arcs = petri.get("arcs")
    if not isinstance(arcs, list) or not arcs:
        errors.append("petri.arcs must be a non-empty array")
        arcs = []
    pairs: set[tuple[str, str]] = set()
    for index, arc in enumerate(arcs):
        path = f"petri.arcs[{index}]"
        if not isinstance(arc, dict):
            errors.append(f"{path} must be an object")
            continue
        for key in set(arc) - {"from", "to", "weight", "bend"}:
            errors.append(f"{path}.{key} is not allowed")
        source, target = arc.get("from"), arc.get("to")
        if not isinstance(source, str) or not isinstance(target, str) or not (
            (source in node_sets["places"] and target in node_sets["transitions"])
            or (source in node_sets["transitions"] and target in node_sets["places"])
        ):
            errors.append(f"{path} must connect one place and one transition")
        elif (source, target) in pairs:
            errors.append(f"{path} duplicates a directed arc; use weight instead")
        else:
            pairs.add((source, target))
        weight = arc.get("weight")
        if type(weight) is not int or weight < 1:
            errors.append(f"{path}.weight must be a positive integer")
        bend = arc.get("bend", 0)
        if not isinstance(bend, (int, float)) or isinstance(bend, bool) or not math.isfinite(bend) or abs(bend) > 80:
            errors.append(f"{path}.bend must be between -80 and 80 degrees")


def validate_spec(spec: dict[str, Any], spec_path: Path | None = None) -> ValidationResult:
    errors: list[str] = []

    for field in ("schema_version", "id", "recipe", "kind"):
        if field not in spec:
            errors.append(f"missing required field: {field}")

    schema_version = spec.get("schema_version")
    if schema_version not in {"1.0", "1.1"}:
        errors.append("schema_version must be '1.0' or '1.1'")

    figure_id = spec.get("id")
    if not isinstance(figure_id, str) or not ID_RE.match(figure_id):
        errors.append("id must match ^[A-Za-z0-9][A-Za-z0-9._-]*$")

    kind = spec.get("kind")
    if kind not in {"pgfplots", "tikz"}:
        errors.append("kind must be 'pgfplots' or 'tikz'")

    if schema_version == "1.0" and ("theme" in spec or "profile" in spec):
        errors.append("theme/profile require schema_version '1.1'")
    if schema_version == "1.1":
        theme = spec.get("theme") or {"id": "journal-muted"}
        profile = spec.get("profile") or {"id": "journal-single-column"}
        if not isinstance(theme, dict) or not isinstance(theme.get("id"), str):
            errors.append("theme.id is required for a structured theme")
        else:
            try:
                load_theme(theme["id"])
            except ValueError as exc:
                errors.append(str(exc))
        if not isinstance(profile, dict) or not isinstance(profile.get("id"), str):
            errors.append("profile.id is required for a structured publication profile")
        else:
            try:
                load_profile(profile["id"])
            except ValueError as exc:
                errors.append(str(exc))

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
        allowed_schema_versions = recipe.get("schema_versions")
        if isinstance(allowed_schema_versions, list) and schema_version not in allowed_schema_versions:
            errors.append(
                f"recipe {recipe_id!r} requires schema_version in {allowed_schema_versions!r}, "
                f"got {schema_version!r}"
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
    if recipe_id == "petri-net":
        if diagram is not None:
            errors.append("petri-net uses petri, not diagram")
        _validate_petri(spec.get("petri"), errors)
    elif "petri" in spec:
        errors.append("petri data requires recipe='petri-net'")
    if diagram is not None:
        if not isinstance(diagram, dict):
            errors.append("diagram must be an object")
        else:
            node_ids = _unique_ids(diagram.get("nodes", []), "diagram.nodes", errors)
            group_ids = _unique_ids(diagram.get("groups", []), "diagram.groups", errors)
            if node_ids & group_ids:
                errors.append(
                    "diagram node/group IDs share one namespace; duplicates: "
                    + ", ".join(sorted(node_ids & group_ids))
                )
            edge_ids: set[str] = set()
            if schema_version == "1.1":
                edge_ids = _unique_ids(diagram.get("edges", []), "diagram.edges", errors)
                layout = diagram.get("layout") or {"type": "relative"}
                if not isinstance(layout, dict):
                    errors.append("diagram.layout must be an object")
                    layout = {"type": "relative"}
                layout_type = layout.get("type")
                if layout_type not in {"manual", "relative", "grid"}:
                    errors.append("diagram.layout.type must be manual, relative, or grid")
                if "auto_fit" in layout and not isinstance(layout["auto_fit"], bool):
                    errors.append("diagram.layout.auto_fit must be a boolean")
                _validate_length(layout.get("row_gap"), "diagram.layout.row_gap", errors)
                _validate_length(layout.get("column_gap"), "diagram.layout.column_gap", errors)

                relative_graph: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
                absolute_roots = 0
                grid_cells: set[tuple[int, int]] = set()
                for index, node in enumerate(diagram.get("nodes", [])):
                    if not isinstance(node, dict):
                        continue
                    allowed_roles = recipe.get("roles") if recipe is not None else None
                    if isinstance(allowed_roles, list):
                        role = node.get("role", "concept")
                        if role not in allowed_roles:
                            errors.append(
                                f"diagram.nodes[{index}].role {role!r} is not allowed by "
                                f"recipe {recipe_id!r}; allowed roles: {allowed_roles!r}"
                            )
                    for legacy in ("at", "right_of", "below_of", "style"):
                        if legacy in node:
                            errors.append(
                                f"diagram.nodes[{index}].{legacy} is legacy 1.0 syntax; use structured 1.1 fields"
                            )
                    position = node.get("position")
                    if not isinstance(position, dict):
                        errors.append(f"diagram.nodes[{index}].position is required in schema 1.1")
                        continue
                    position_type = position.get("type")
                    if position_type == "absolute":
                        absolute_roots += 1
                        if layout_type == "grid":
                            errors.append(f"diagram.nodes[{index}] grid layout requires grid position")
                    elif position_type == "relative":
                        target = position.get("of")
                        if target not in node_ids:
                            errors.append(
                                f"diagram.nodes[{index}].position.of references unknown node: {target!r}"
                            )
                        else:
                            relative_graph[node["id"]].add(target)
                        _validate_length(position.get("gap"), f"diagram.nodes[{index}].position.gap", errors)
                        if layout_type == "manual":
                            errors.append(f"diagram.nodes[{index}] manual layout requires absolute position")
                        if layout_type == "grid":
                            errors.append(f"diagram.nodes[{index}] grid layout requires grid position")
                    elif position_type == "grid":
                        row, column = position.get("row"), position.get("column")
                        if not isinstance(row, int) or row < 0 or not isinstance(column, int) or column < 0:
                            errors.append(f"diagram.nodes[{index}] grid row/column must be non-negative integers")
                        elif (row, column) in grid_cells:
                            errors.append(f"diagram.nodes[{index}] duplicates grid cell ({row},{column})")
                        else:
                            grid_cells.add((row, column))
                        if layout_type != "grid":
                            errors.append(f"diagram.nodes[{index}] grid position requires diagram.layout.type=grid")
                    else:
                        errors.append(f"diagram.nodes[{index}].position.type is invalid: {position_type!r}")
                    for field in ("text_width", "min_width", "min_height"):
                        _validate_length(node.get(field), f"diagram.nodes[{index}].{field}", errors)

                if layout_type == "relative" and node_ids and absolute_roots == 0:
                    errors.append("relative layout requires at least one absolute root node")
                if _has_cycle(relative_graph):
                    errors.append("diagram relative-position dependencies must not contain a cycle")

                group_graph: dict[str, set[str]] = {group_id: set() for group_id in group_ids}
                parent_count: dict[str, int] = {}
                valid_members = node_ids | group_ids
                for index, group in enumerate(diagram.get("groups", [])):
                    if not isinstance(group, dict):
                        continue
                    _validate_length(group.get("padding"), f"diagram.groups[{index}].padding", errors)
                    for member in group.get("members", []):
                        if member not in valid_members:
                            errors.append(
                                f"diagram.groups[{index}].members references unknown node/group: {member!r}"
                            )
                            continue
                        if member == group.get("id"):
                            errors.append(f"diagram.groups[{index}] cannot contain itself")
                        parent_count[member] = parent_count.get(member, 0) + 1
                        if member in group_ids:
                            group_graph[group["id"]].add(member)
                for member, count in parent_count.items():
                    if count > 1:
                        errors.append(f"diagram member {member!r} has more than one direct parent group")
                if _has_cycle(group_graph):
                    errors.append("diagram group containment must not contain a cycle")

            edge_target_graph: dict[str, set[str]] = {edge_id: set() for edge_id in edge_ids}
            for index, edge in enumerate(diagram.get("edges", [])):
                if not isinstance(edge, dict):
                    errors.append(f"diagram.edges[{index}] must be an object")
                    continue
                if edge.get("from") not in node_ids:
                    errors.append(
                        f"diagram.edges[{index}].from references unknown node: {edge.get('from')!r}"
                    )
                if schema_version != "1.1":
                    if edge.get("to") not in node_ids:
                        errors.append(
                            f"diagram.edges[{index}].to references unknown node: {edge.get('to')!r}"
                        )
                    if "to_edge" in edge:
                        errors.append(f"diagram.edges[{index}].to_edge requires schema 1.1")
                else:
                    has_to = isinstance(edge.get("to"), str) and bool(edge.get("to"))
                    has_to_edge = isinstance(edge.get("to_edge"), str) and bool(edge.get("to_edge"))
                    if has_to == has_to_edge:
                        errors.append(f"diagram.edges[{index}] requires exactly one of to or to_edge")
                    elif has_to:
                        if edge.get("to") not in node_ids:
                            errors.append(
                                f"diagram.edges[{index}].to references unknown node: {edge.get('to')!r}"
                            )
                    else:
                        target_edge = edge.get("to_edge")
                        if recipe_id != "relation-diagram":
                            errors.append(
                                f"diagram.edges[{index}].to_edge is only supported by relation-diagram"
                            )
                        if target_edge not in edge_ids:
                            errors.append(
                                f"diagram.edges[{index}].to_edge references unknown edge: {target_edge!r}"
                            )
                        elif edge.get("id") == target_edge:
                            errors.append(f"diagram.edges[{index}] cannot target itself with to_edge")
                        elif edge.get("id") in edge_target_graph:
                            edge_target_graph[edge["id"]].add(target_edge)
                        if edge.get("to_anchor"):
                            errors.append(f"diagram.edges[{index}].to_anchor is not valid with to_edge")
                    if "label_sloped" in edge and not isinstance(edge["label_sloped"], bool):
                        errors.append(f"diagram.edges[{index}].label_sloped must be a boolean")
                    route = edge.get("route", "straight")
                    routing = edge.get("routing") or {}
                    if route == "loop" and (has_to_edge or edge.get("from") != edge.get("to")):
                        errors.append(f"diagram.edges[{index}] route=loop requires from == to")
                    if has_to and edge.get("from") == edge.get("to") and route != "loop":
                        errors.append(f"diagram.edges[{index}] self-edge requires route=loop")
                    if not isinstance(routing, dict):
                        errors.append(f"diagram.edges[{index}].routing must be an object")
                    else:
                        if route == "orthogonal" and any(key in routing for key in ("bend", "side")):
                            errors.append(f"diagram.edges[{index}] orthogonal routing accepts only order")
                        if route == "curve" and any(key in routing for key in ("order", "side")):
                            errors.append(f"diagram.edges[{index}] curve routing accepts only bend")
                        if route == "loop" and any(key in routing for key in ("order", "bend")):
                            errors.append(f"diagram.edges[{index}] loop routing accepts only side")
                        if route == "straight" and routing:
                            errors.append(f"diagram.edges[{index}] straight route does not accept routing options")
            if schema_version == "1.1" and _has_cycle(edge_target_graph):
                errors.append("diagram edge-to-edge target dependencies must not contain a cycle")

    outputs = spec.get("outputs", {})
    if outputs is not None and not isinstance(outputs, dict):
        errors.append("outputs must be an object")
    elif isinstance(outputs, dict):
        basename = outputs.get("basename", "figure")
        if not isinstance(basename, str) or not ID_RE.match(basename):
            errors.append("outputs.basename must be a safe file basename")
        formats = outputs.get("formats", ["pdf"])
        if not isinstance(formats, list) or not formats:
            errors.append("outputs.formats must be a non-empty array")
        elif any(item not in {"pdf", "svg"} for item in formats):
            errors.append("outputs.formats accepts only pdf and svg")
        elif len(set(formats)) != len(formats):
            errors.append("outputs.formats must not contain duplicates")
        elif "pdf" not in formats:
            errors.append("outputs.formats must include pdf as the canonical artifact")

    return ValidationResult(tuple(errors))


def load_and_validate(path: str | Path) -> tuple[dict[str, Any], ValidationResult]:
    spec_path = Path(path).resolve()
    spec = load_json(spec_path)
    return spec, validate_spec(spec, spec_path)
