from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .design import validate_design
from .expert import build_expert
from .generative_geometry import GeometryError, delaunay_triangles, l_system_paths, safe_expression, split_box_edge_occlusion, voronoi_cells
from .io import load_json, write_json_atomic
from .qa import _render_preview
from .raster_compare import RasterError, ink_distance, normalized_ink, read_gray_image


class GenerativeError(RuntimeError):
    pass


SUPPORTED_GENERATORS = {
    "ring_nodes",
    "boundary_circle",
    "complete_edges",
    "circulant_edges",
    "star_polygon",
    "center_node",
    "center_spokes",
    "line_nodes",
    "complete_bipartite_edges",
    "lattice_nodes",
    "lattice_edges",
    "lattice_cells",
    "parametric_curve",
    "koch_snowflake",
    "projected_box",
    "projected_prism",
    "point_nodes",
    "delaunay_edges",
    "voronoi_cells",
    "l_system",
    "truchet_tiles",
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not cleaned or cleaned[0].isdigit():
        cleaned = "g_" + cleaned
    return cleaned


def _sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _require_number(params: dict[str, Any], key: str, *, minimum: float | None = None) -> float:
    value = params.get(key)
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise GenerativeError(f"generator parameter {key!r} must be a finite number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise GenerativeError(f"generator parameter {key!r} must be at least {minimum}")
    return result


def _require_int(params: dict[str, Any], key: str, *, minimum: int = 1) -> int:
    value = params.get(key)
    if type(value) is not int or value < minimum:
        raise GenerativeError(f"generator parameter {key!r} must be an integer >= {minimum}")
    return value


def _ring_name(generator_id: str, index: int) -> str:
    return f"{_safe_name(generator_id)}_{index:03d}"


def _node_name(generator_id: str, *indices: int) -> str:
    suffix = "_".join(f"{index:03d}" for index in indices)
    return f"{_safe_name(generator_id)}_{suffix}"


def _require_pair(params: dict[str, Any], key: str, default: tuple[float, float] | None = None) -> tuple[float, float]:
    value = params.get(key, default)
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise GenerativeError(f"generator parameter {key!r} must be a two-number array")
    if any(type(item) not in (int, float) or not math.isfinite(float(item)) for item in value):
        raise GenerativeError(f"generator parameter {key!r} must contain finite numbers")
    return float(value[0]), float(value[1])


def _require_triplet(params: dict[str, Any], key: str, default: tuple[float, float, float] | None = None) -> tuple[float, float, float]:
    value = params.get(key, default)
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise GenerativeError(f"generator parameter {key!r} must be a three-number array")
    if any(type(item) not in (int, float) or not math.isfinite(float(item)) for item in value):
        raise GenerativeError(f"generator parameter {key!r} must contain finite numbers")
    return float(value[0]), float(value[1]), float(value[2])


def _koch_segment(start: tuple[float, float], end: tuple[float, float], depth: int, turn_sign: float = -1.0) -> list[tuple[float, float]]:
    if depth == 0:
        return [start, end]
    x1, y1 = start
    x2, y2 = end
    dx = (x2 - x1) / 3.0
    dy = (y2 - y1) / 3.0
    a = (x1 + dx, y1 + dy)
    b = (x1 + 2.0 * dx, y1 + 2.0 * dy)
    angle = turn_sign * math.pi / 3.0
    peak = (
        a[0] + dx * math.cos(angle) - dy * math.sin(angle),
        a[1] + dx * math.sin(angle) + dy * math.cos(angle),
    )
    parts = [
        _koch_segment(start, a, depth - 1, turn_sign),
        _koch_segment(a, peak, depth - 1, turn_sign),
        _koch_segment(peak, b, depth - 1, turn_sign),
        _koch_segment(b, end, depth - 1, turn_sign),
    ]
    merged = parts[0][:]
    for part in parts[1:]:
        merged.extend(part[1:])
    return merged


def _parametric_points(params: dict[str, Any]) -> list[tuple[float, float]]:
    family = params.get("family")
    samples = _require_int(params, "samples", minimum=16)
    if samples > 4000:
        raise GenerativeError("parametric_curve samples must be <= 4000")
    t_min = float(params.get("t_min", 0.0))
    t_max = float(params.get("t_max", 2.0 * math.pi))
    if not math.isfinite(t_min) or not math.isfinite(t_max) or t_max <= t_min:
        raise GenerativeError("parametric_curve requires finite t_min < t_max")

    expression_x = expression_y = None
    if family == "expression":
        expression_x = safe_expression(params.get("x"))
        expression_y = safe_expression(params.get("y"))

    def sample(t: float) -> tuple[float, float]:
        if family == "expression":
            return expression_x(t), expression_y(t)
        if family == "rose":
            amplitude = float(params.get("amplitude", 3.0))
            petals = float(params.get("petals", 5.0))
            phase = math.radians(float(params.get("phase_deg", 0.0)))
            radius = amplitude * math.cos(petals * t + phase)
            return radius * math.cos(t), radius * math.sin(t)
        if family == "lissajous":
            ax = float(params.get("amplitude_x", 3.0))
            ay = float(params.get("amplitude_y", 3.0))
            fx = float(params.get("frequency_x", 3.0))
            fy = float(params.get("frequency_y", 2.0))
            phase = math.radians(float(params.get("phase_deg", 90.0)))
            return ax * math.sin(fx * t + phase), ay * math.sin(fy * t)
        if family == "spiral":
            a = float(params.get("a", 0.15))
            b = float(params.get("b", 0.16))
            radius = a + b * t
            return radius * math.cos(t), radius * math.sin(t)
        raise GenerativeError("parametric_curve family must be rose, lissajous, spiral, or expression")

    return [sample(t_min + (t_max - t_min) * index / (samples - 1)) for index in range(samples)]


def _project3(point: tuple[float, float, float], px: tuple[float, float], py: tuple[float, float], pz: tuple[float, float]) -> tuple[float, float]:
    x, y, z = point
    return x * px[0] + y * py[0] + z * pz[0], x * px[1] + y * py[1] + z * pz[1]


def _auto_density(node_count: int, edge_count: int, density: dict[str, Any]) -> dict[str, float]:
    target = density.get("target", "balanced")
    factor = {"light": 0.82, "balanced": 1.0, "dense": 1.13}.get(target)
    if factor is None:
        raise GenerativeError("visual_density.target must be light, balanced, or dense")
    base_width = 0.56 / (1.0 + 0.08 * math.sqrt(max(edge_count, 1)))
    base_opacity = 0.28 + 0.35 / (1.0 + max(edge_count, 0) / 40.0)
    resolved = {
        "edge_line_width_pt": _clamp(base_width * factor, 0.14, 0.72),
        "edge_opacity": _clamp(base_opacity * (0.92 if target == "light" else 1.0), 0.20, 0.72),
        "boundary_line_width_pt": 0.48,
        "boundary_opacity": 0.60,
        "node_outline_pt": _clamp(0.54 + 0.008 * min(node_count, 24), 0.52, 0.72),
        "node_outline_opacity": 0.66,
    }
    for key in tuple(resolved):
        if key in density:
            value = density[key]
            if type(value) not in (int, float) or not math.isfinite(float(value)):
                raise GenerativeError(f"visual_density.{key} must be a finite number")
            resolved[key] = float(value)
    resolved["edge_line_width_pt"] = _clamp(resolved["edge_line_width_pt"], 0.05, 2.0)
    resolved["edge_opacity"] = _clamp(resolved["edge_opacity"], 0.02, 1.0)
    resolved["boundary_opacity"] = _clamp(resolved["boundary_opacity"], 0.02, 1.0)
    resolved["node_outline_opacity"] = _clamp(resolved["node_outline_opacity"], 0.02, 1.0)
    return resolved


def _resolve_model(design: dict[str, Any]) -> dict[str, Any]:
    model = design.get("structure_model")
    if not isinstance(model, dict):
        raise GenerativeError("generative rendering requires structure_model in figure.design.json")
    coordinate_system = model.get("coordinate_system")
    if coordinate_system not in {"polar", "cartesian", "isometric", "3d", "abstract"}:
        raise GenerativeError(f"unsupported coordinate_system: {coordinate_system}")
    generators = model.get("generators") or []
    if not isinstance(generators, list) or not generators:
        raise GenerativeError("structure_model.generators must contain at least one generator")
    seen_ids: set[str] = set()
    generator_map: dict[str, dict[str, Any]] = {}
    for item in generators:
        if not isinstance(item, dict):
            raise GenerativeError("each structure generator must be an object")
        generator_id = item.get("id")
        generator_type = item.get("type")
        if not isinstance(generator_id, str) or not generator_id.strip():
            raise GenerativeError("each structure generator needs a nonempty id")
        if generator_id in seen_ids:
            raise GenerativeError(f"duplicate structure generator id: {generator_id}")
        seen_ids.add(generator_id)
        if generator_type not in SUPPORTED_GENERATORS:
            raise GenerativeError(f"unsupported structure generator type: {generator_type}")
        generator_map[generator_id] = item

    nodes: dict[str, tuple[float, float]] = {}
    groups: dict[str, list[str]] = {}
    group_node_radius: dict[str, float] = {}
    rings: dict[str, list[str]] = {}
    lattices: dict[str, list[list[str]]] = {}
    point_groups: dict[str, list[str]] = {}
    center_nodes: dict[str, dict[str, Any]] = {}
    boundaries: list[dict[str, Any]] = []
    edges: set[tuple[str, str]] = set()
    polygons: list[dict[str, Any]] = []
    curves: list[dict[str, Any]] = []
    boxes: list[dict[str, Any]] = []

    for item in generators:
        params = item.get("parameters") or {}
        kind = item["type"]
        if kind == "ring_nodes":
            if coordinate_system not in {"polar", "abstract"}:
                raise GenerativeError("ring_nodes requires coordinate_system polar or abstract")
            count = _require_int(params, "count", minimum=3)
            radius = _require_number(params, "radius", minimum=0.01)
            phase = float(params.get("phase_deg", 90.0))
            ring_names: list[str] = []
            for index in range(count):
                angle = math.radians(phase - 360.0 * index / count)
                name = _ring_name(item["id"], index)
                nodes[name] = (radius * math.cos(angle), radius * math.sin(angle))
                ring_names.append(name)
            rings[item["id"]] = ring_names
            groups[item["id"]] = ring_names
            group_node_radius[item["id"]] = float(params.get("node_radius", 0.30))
        elif kind == "line_nodes":
            if coordinate_system not in {"cartesian", "abstract"}:
                raise GenerativeError("line_nodes requires coordinate_system cartesian or abstract")
            count = _require_int(params, "count", minimum=1)
            start = _require_pair(params, "start", (0.0, 0.0))
            end = _require_pair(params, "end", (4.0, 0.0))
            names: list[str] = []
            for index in range(count):
                fraction = 0.5 if count == 1 else index / (count - 1)
                point = (start[0] + (end[0] - start[0]) * fraction, start[1] + (end[1] - start[1]) * fraction)
                name = _node_name(item["id"], index)
                nodes[name] = point
                names.append(name)
            groups[item["id"]] = names
            group_node_radius[item["id"]] = float(params.get("node_radius", 0.22))
        elif kind == "lattice_nodes":
            if coordinate_system not in {"cartesian", "isometric", "abstract"}:
                raise GenerativeError("lattice_nodes requires coordinate_system cartesian, isometric, or abstract")
            rows = _require_int(params, "rows", minimum=1)
            cols = _require_int(params, "cols", minimum=1)
            if rows * cols > 10000:
                raise GenerativeError("lattice_nodes may generate at most 10000 nodes")
            origin = _require_pair(params, "origin", (0.0, 0.0))
            basis_u = _require_pair(params, "basis_u", (1.0, 0.0))
            basis_v = _require_pair(params, "basis_v", (0.0, 1.0))
            grid: list[list[str]] = []
            names: list[str] = []
            for row in range(rows):
                grid_row: list[str] = []
                for col in range(cols):
                    name = _node_name(item["id"], row, col)
                    point = (
                        origin[0] + col * basis_u[0] + row * basis_v[0],
                        origin[1] + col * basis_u[1] + row * basis_v[1],
                    )
                    nodes[name] = point
                    grid_row.append(name)
                    names.append(name)
                grid.append(grid_row)
            lattices[item["id"]] = grid
            groups[item["id"]] = names
            group_node_radius[item["id"]] = float(params.get("node_radius", 0.09))
        elif kind == "point_nodes":
            raw_points = params.get("points")
            if not isinstance(raw_points, list) or not 2 <= len(raw_points) <= 128:
                raise GenerativeError("point_nodes points must contain 2–128 coordinate pairs")
            points = [_require_pair({"point": point}, "point") for point in raw_points]
            if len(set(points)) != len(points):
                raise GenerativeError("point_nodes points must be distinct")
            names = []
            for index, point in enumerate(points):
                name = _node_name(item["id"], index)
                nodes[name] = point
                names.append(name)
            groups[item["id"]] = names
            point_groups[item["id"]] = names
            group_node_radius[item["id"]] = float(params.get("node_radius", 0.07))

    for item in generators:
        params = item.get("parameters") or {}
        kind = item["type"]
        if kind == "center_node":
            name = _safe_name(item["id"])
            if name in nodes:
                raise GenerativeError(f"duplicate generated node name: {name}")
            nodes[name] = (float(params.get("x", 0.0)), float(params.get("y", 0.0)))
            center_nodes[item["id"]] = {"name": name, **params}
        elif kind == "boundary_circle":
            radius = params.get("radius")
            ring_id = params.get("nodes")
            if radius is None and ring_id in generator_map:
                radius = (generator_map[ring_id].get("parameters") or {}).get("radius")
            if type(radius) not in (int, float) or float(radius) <= 0:
                raise GenerativeError("boundary_circle requires a positive radius or a valid nodes ring")
            boundaries.append({"radius": float(radius), "id": item["id"]})

    for item in generators:
        params = item.get("parameters") or {}
        kind = item["type"]
        if kind == "parametric_curve":
            curves.append({"id": item["id"], "points": _parametric_points(params), "closed": bool(params.get("closed", params.get("family") in {"rose", "lissajous"}))})
        elif kind == "l_system":
            paths = l_system_paths(
                params.get("axiom", "F"), params.get("rules", {}),
                params.get("depth", 0), _require_number(params, "angle_deg"),
                _require_number(params, "step", minimum=0.000001),
                _require_pair(params, "origin", (0.0, 0.0)),
                float(params.get("heading_deg", 0.0)),
            )
            curves.extend({"id": item["id"], "points": path, "closed": False} for path in paths)
        elif kind == "truchet_tiles":
            if coordinate_system not in {"cartesian", "isometric", "abstract"}:
                raise GenerativeError("truchet_tiles requires Cartesian or isometric coordinates")
            rows = _require_int(params, "rows")
            cols = _require_int(params, "cols")
            if rows*cols > 1000:
                raise GenerativeError("truchet_tiles may generate at most 1000 tiles")
            origin = _require_pair(params, "origin", (0.0, 0.0))
            basis_u = _require_pair(params, "basis_u", (1.0, 0.0))
            basis_v = _require_pair(params, "basis_v", (0.0, 1.0))
            if abs(basis_u[0]*basis_v[1]-basis_u[1]*basis_v[0]) < 1e-9:
                raise GenerativeError("truchet_tiles basis vectors must be independent")
            seed = params.get("seed", 0)
            if type(seed) is not int or not 0 <= seed <= 2**31-1:
                raise GenerativeError("truchet_tiles seed must be a nonnegative 31-bit integer")
            samples = _require_int({"samples": params.get("samples", 9)}, "samples", minimum=4)
            if samples > 64:
                raise GenerativeError("truchet_tiles samples must be <= 64")
            pattern = params.get("pattern", "hash")
            if pattern not in {"hash", "checkerboard"}:
                raise GenerativeError("truchet_tiles pattern must be hash or checkerboard")
            for row in range(rows):
                for col in range(cols):
                    flip = ((row+col+seed) % 2 if pattern == "checkerboard" else hashlib.sha256(f"{seed}:{row}:{col}".encode()).digest()[0] & 1)
                    arcs = (((0.0, 0.0, 0.0), (1.0, 1.0, math.pi)) if not flip else
                            ((0.0, 1.0, -math.pi/2), (1.0, 0.0, math.pi/2)))
                    for center_u, center_v, start_angle in arcs:
                        points = []
                        for index in range(samples):
                            angle = start_angle + (math.pi/2)*index/(samples-1)
                            u = col+center_u+0.5*math.cos(angle)
                            v = row+center_v+0.5*math.sin(angle)
                            points.append((origin[0]+u*basis_u[0]+v*basis_v[0],
                                           origin[1]+u*basis_u[1]+v*basis_v[1]))
                        curves.append({"id": item["id"], "points": points, "closed": False})
        elif kind == "koch_snowflake":
            depth = _require_int(params, "depth", minimum=0)
            if depth > 6:
                raise GenerativeError("koch_snowflake depth must be <= 6")
            radius = _require_number(params, "radius", minimum=0.01)
            center = _require_pair(params, "center", (0.0, 0.0))
            rotation = math.radians(float(params.get("rotation_deg", 90.0)))
            vertices = [
                (center[0] + radius * math.cos(rotation + 2.0 * math.pi * index / 3.0), center[1] + radius * math.sin(rotation + 2.0 * math.pi * index / 3.0))
                for index in range(3)
            ]
            points: list[tuple[float, float]] = []
            for index in range(3):
                segment = _koch_segment(vertices[index], vertices[(index + 1) % 3], depth, turn_sign=-1.0)
                if points:
                    points.extend(segment[1:])
                else:
                    points.extend(segment)
            curves.append({"id": item["id"], "points": points, "closed": True})
        elif kind == "projected_box":
            if coordinate_system not in {"3d", "isometric", "abstract"}:
                raise GenerativeError("projected_box requires coordinate_system 3d, isometric, or abstract")
            origin = _require_triplet(params, "origin", (0.0, 0.0, 0.0))
            size = _require_triplet(params, "size", (3.0, 2.0, 2.0))
            if any(value <= 0 for value in size):
                raise GenerativeError("projected_box size values must be positive")
            px = _require_pair(params, "project_x", (0.92, -0.36))
            py = _require_pair(params, "project_y", (-0.92, -0.36))
            pz = _require_pair(params, "project_z", (0.0, 1.0))
            vertices3 = {
                (ix, iy, iz): (origin[0] + ix * size[0], origin[1] + iy * size[1], origin[2] + iz * size[2])
                for ix in (0, 1) for iy in (0, 1) for iz in (0, 1)
            }
            projected = {key: _project3(value, px, py, pz) for key, value in vertices3.items()}
            visibility = params.get("visibility", "wireframe")
            if visibility not in {"wireframe", "hidden_dashed", "visible_only"}:
                raise GenerativeError("projected_box visibility must be wireframe, hidden_dashed, or visible_only")
            cross_occlusion = params.get("occlude_other_boxes", False)
            if type(cross_occlusion) is not bool:
                raise GenerativeError("projected_box occlude_other_boxes must be boolean")
            if cross_occlusion and visibility == "wireframe":
                raise GenerativeError("projected_box cross-box occlusion requires hidden_dashed or visible_only")
            # Orthographic camera is the null direction of the projection matrix.
            # Cross the projection rows: (px.x,py.x,pz.x) x (px.y,py.y,pz.y).
            camera = (py[0]*pz[1]-pz[0]*py[1], pz[0]*px[1]-px[0]*pz[1], px[0]*py[1]-py[0]*px[1])
            if math.hypot(*camera) < 1e-9:
                raise GenerativeError("projected_box projection basis has no camera direction")
            if "camera_direction" in params:
                camera = _require_triplet(params, "camera_direction")
                norm = math.hypot(*camera)
                if norm < 1e-9:
                    raise GenerativeError("projected_box camera_direction must be nonzero")
                for screen_axis in ((px[0], py[0], pz[0]), (px[1], py[1], pz[1])):
                    if abs(sum(a*b for a, b in zip(camera, screen_axis))) > 1e-6*norm*math.hypot(*screen_axis):
                        raise GenerativeError("projected_box camera_direction must be perpendicular to projection rows")
            elif sum(camera) < 0:
                camera = tuple(-component for component in camera)
            boxes.append({"id": item["id"], "origin": origin, "size": size, "px": px, "py": py, "pz": pz,
                          "camera": camera, "visibility": visibility, "occlude": cross_occlusion})
            def add_box_edge(a: tuple[int, int, int], b: tuple[int, int, int]) -> None:
                fixed = [axis for axis in range(3) if a[axis] == b[axis]]
                visible = any((1 if a[axis] else -1) * camera[axis] > 1e-9 for axis in fixed)
                if visibility == "visible_only" and not visible:
                    return
                curves.append({"id": item["id"], "points": [projected[a], projected[b]], "closed": False,
                               "style": "hidden" if visibility == "hidden_dashed" and not visible else "visible",
                               "box_id": item["id"], "start3": vertices3[a], "end3": vertices3[b]})
            for ix in (0, 1):
                for iy in (0, 1):
                    add_box_edge((ix, iy, 0), (ix, iy, 1))
            for iz in (0, 1):
                for iy in (0, 1):
                    add_box_edge((0, iy, iz), (1, iy, iz))
                for ix in (0, 1):
                    add_box_edge((ix, 0, iz), (ix, 1, iz))
        elif kind == "projected_prism":
            if coordinate_system not in {"3d", "isometric", "abstract"}:
                raise GenerativeError("projected_prism requires coordinate_system 3d, isometric, or abstract")
            sides = _require_int(params, "sides", minimum=3)
            if sides > 64:
                raise GenerativeError("projected_prism sides must be <= 64")
            radius = _require_number(params, "radius", minimum=0.000001)
            height = _require_number(params, "height", minimum=0.000001)
            origin = _require_triplet(params, "origin", (0.0, 0.0, 0.0))
            rotation = math.radians(float(params.get("rotation_deg", 0.0)))
            if not math.isfinite(rotation):
                raise GenerativeError("projected_prism rotation_deg must be finite")
            px = _require_pair(params, "project_x", (0.92, -0.36))
            py = _require_pair(params, "project_y", (-0.92, -0.36))
            pz = _require_pair(params, "project_z", (0.0, 1.0))
            visibility = params.get("visibility", "wireframe")
            if visibility not in {"wireframe", "hidden_dashed", "visible_only"}:
                raise GenerativeError("projected_prism visibility must be wireframe, hidden_dashed, or visible_only")
            camera = (py[0]*pz[1]-pz[0]*py[1], pz[0]*px[1]-px[0]*pz[1], px[0]*py[1]-py[0]*px[1])
            if math.hypot(*camera) < 1e-9:
                raise GenerativeError("projected_prism projection basis has no camera direction")
            if "camera_direction" in params:
                camera = _require_triplet(params, "camera_direction")
                norm = math.hypot(*camera)
                if norm < 1e-9:
                    raise GenerativeError("projected_prism camera_direction must be nonzero")
                for screen_axis in ((px[0], py[0], pz[0]), (px[1], py[1], pz[1])):
                    if abs(sum(a*b for a, b in zip(camera, screen_axis))) > 1e-6*norm*math.hypot(*screen_axis):
                        raise GenerativeError("projected_prism camera_direction must be perpendicular to projection rows")
            elif sum(camera) < 0:
                camera = tuple(-component for component in camera)

            bottom3: list[tuple[float, float, float]] = []
            top3: list[tuple[float, float, float]] = []
            for index in range(sides):
                angle = rotation + 2.0 * math.pi * index / sides
                base = (
                    origin[0] + radius * math.cos(angle),
                    origin[1] + radius * math.sin(angle),
                    origin[2],
                )
                bottom3.append(base)
                top3.append((base[0], base[1], base[2] + height))

            side_normals: list[tuple[float, float, float]] = []
            for index in range(sides):
                a = bottom3[index]
                b = bottom3[(index + 1) % sides]
                dx, dy = b[0] - a[0], b[1] - a[1]
                side_normals.append((dy, -dx, 0.0))

            def face_front(normal: tuple[float, float, float]) -> bool:
                return sum(a*b for a, b in zip(normal, camera)) > 1e-9

            top_front = face_front((0.0, 0.0, 1.0))
            bottom_front = face_front((0.0, 0.0, -1.0))
            side_front = [face_front(normal) for normal in side_normals]

            def add_prism_edge(a3: tuple[float, float, float], b3: tuple[float, float, float], visible: bool) -> None:
                if visibility == "visible_only" and not visible:
                    return
                curves.append({
                    "id": item["id"],
                    "points": [_project3(a3, px, py, pz), _project3(b3, px, py, pz)],
                    "closed": False,
                    "style": "hidden" if visibility == "hidden_dashed" and not visible else "visible",
                })

            for index in range(sides):
                next_index = (index + 1) % sides
                add_prism_edge(bottom3[index], bottom3[next_index], bottom_front or side_front[index])
                add_prism_edge(top3[index], top3[next_index], top_front or side_front[index])
                add_prism_edge(
                    bottom3[index],
                    top3[index],
                    side_front[index] or side_front[(index - 1) % sides],
                )

    for item in generators:
        params = item.get("parameters") or {}
        kind = item["type"]
        if kind in {"complete_edges", "circulant_edges", "star_polygon"}:
            ring_id = params.get("nodes")
            ring = rings.get(str(ring_id))
            if not ring:
                raise GenerativeError(f"{kind} references unknown ring_nodes generator: {ring_id}")
            count = len(ring)
            if kind == "complete_edges":
                for left in range(count):
                    for right in range(left + 1, count):
                        edges.add((ring[left], ring[right]))
            else:
                raw_steps = params.get("steps") if kind == "circulant_edges" else [params.get("step", 2)]
                if type(raw_steps) is int:
                    raw_steps = [raw_steps]
                if not isinstance(raw_steps, list) or not raw_steps:
                    raise GenerativeError(f"{kind} requires one or more integer steps")
                for step in raw_steps:
                    if type(step) is not int or step <= 0 or step >= count:
                        raise GenerativeError(f"{kind} step values must be integers between 1 and {count - 1}")
                    for index in range(count):
                        other = (index + step) % count
                        pair = tuple(sorted((ring[index], ring[other])))
                        if pair[0] != pair[1]:
                            edges.add(pair)
        elif kind == "center_spokes":
            ring_id = params.get("nodes")
            center_id = params.get("center")
            ring = rings.get(str(ring_id))
            center = center_nodes.get(str(center_id))
            if not ring or not center:
                raise GenerativeError("center_spokes requires valid nodes and center generator ids")
            for name in ring:
                edges.add(tuple(sorted((name, center["name"]))))
        elif kind == "complete_bipartite_edges":
            left = groups.get(str(params.get("left")))
            right = groups.get(str(params.get("right")))
            if not left or not right:
                raise GenerativeError("complete_bipartite_edges requires valid left and right node-group ids")
            for left_name in left:
                for right_name in right:
                    if left_name != right_name:
                        edges.add(tuple(sorted((left_name, right_name))))
        elif kind == "lattice_edges":
            lattice_id = str(params.get("nodes"))
            grid = lattices.get(lattice_id)
            if not grid:
                raise GenerativeError(f"lattice_edges references unknown lattice_nodes generator: {lattice_id}")
            raw_steps = params.get("neighbor_steps", [[1, 0], [0, 1]])
            if not isinstance(raw_steps, list) or not raw_steps:
                raise GenerativeError("lattice_edges neighbor_steps must be a nonempty array")
            steps: list[tuple[int, int]] = []
            for step in raw_steps:
                if not isinstance(step, (list, tuple)) or len(step) != 2 or any(type(value) is not int for value in step):
                    raise GenerativeError("lattice_edges neighbor_steps entries must be [row_delta, col_delta] integer pairs")
                if step[0] == 0 and step[1] == 0:
                    raise GenerativeError("lattice_edges neighbor step cannot be [0,0]")
                steps.append((int(step[0]), int(step[1])))
            wrap = bool(params.get("wrap", False))
            rows = len(grid)
            cols = len(grid[0]) if rows else 0
            for row in range(rows):
                for col in range(cols):
                    for dr, dc in steps:
                        rr = row + dr
                        cc = col + dc
                        if wrap:
                            rr %= rows
                            cc %= cols
                        elif rr < 0 or rr >= rows or cc < 0 or cc >= cols:
                            continue
                        edges.add(tuple(sorted((grid[row][col], grid[rr][cc]))))
        elif kind == "lattice_cells":
            lattice_id = str(params.get("nodes"))
            grid = lattices.get(lattice_id)
            if not grid:
                raise GenerativeError(f"lattice_cells references unknown lattice_nodes generator: {lattice_id}")
            cell_mode = params.get("cell_mode", "parallelogram")
            if cell_mode not in {"parallelogram", "triangles"}:
                raise GenerativeError("lattice_cells cell_mode must be parallelogram or triangles")
            rows = len(grid)
            cols = len(grid[0]) if rows else 0
            for row in range(rows - 1):
                for col in range(cols - 1):
                    p00 = nodes[grid[row][col]]
                    p01 = nodes[grid[row][col + 1]]
                    p10 = nodes[grid[row + 1][col]]
                    p11 = nodes[grid[row + 1][col + 1]]
                    fill_opacity = float(params.get("fill_opacity", 0.035))
                    if cell_mode == "triangles":
                        polygons.extend([
                            {"id": item["id"], "points": [p00, p01, p10], "fill_opacity": fill_opacity},
                            {"id": item["id"], "points": [p01, p11, p10], "fill_opacity": fill_opacity},
                        ])
                    else:
                        polygons.append({"id": item["id"], "points": [p00, p01, p11, p10], "fill_opacity": fill_opacity})
        elif kind in {"delaunay_edges", "voronoi_cells"}:
            names = point_groups.get(str(params.get("nodes")))
            if not names:
                raise GenerativeError(f"{kind} references unknown point_nodes generator")
            points = [nodes[name] for name in names]
            if kind == "delaunay_edges":
                for a, b, c in delaunay_triangles(points):
                    for i, j in ((a, b), (b, c), (c, a)):
                        edges.add(tuple(sorted((names[i], names[j]))))
            else:
                raw_bounds = params.get("bounds")
                if not isinstance(raw_bounds, list) or len(raw_bounds) != 4 or any(type(value) not in (int, float) for value in raw_bounds):
                    raise GenerativeError("voronoi_cells bounds must be [xmin,ymin,xmax,ymax]")
                cells = voronoi_cells(points, tuple(float(value) for value in raw_bounds))
                fill_opacity = _require_number({"fill_opacity": params.get("fill_opacity", 0.035)}, "fill_opacity", minimum=0)
                polygons.extend({"id": item["id"], "points": cell, "fill_opacity": fill_opacity} for cell in cells if len(cell) >= 3)

    if any(box["occlude"] for box in boxes):
        reference = boxes[0]
        for box in boxes[1:]:
            for key in ("px", "py", "pz"):
                if any(abs(a-b) > 1e-8 for a, b in zip(box[key], reference[key])):
                    raise GenerativeError("cross-box occlusion requires one shared projection basis")
            a, b = box["camera"], reference["camera"]
            similarity = sum(x*y for x, y in zip(a, b))/(math.hypot(*a)*math.hypot(*b))
            if similarity < 1-1e-8:
                raise GenerativeError("cross-box occlusion requires one camera direction")
        by_id = {box["id"]: box for box in boxes}
        resolved_curves = []
        for curve in curves:
            box = by_id.get(curve.get("box_id"))
            if not box or not box["occlude"] or curve.get("style") == "hidden":
                resolved_curves.append(curve)
                continue
            occluders = [(other["origin"], other["size"]) for other in boxes if other["id"] != box["id"]]
            for a, b, covered in split_box_edge_occlusion(curve["start3"], curve["end3"], occluders, box["camera"]):
                if covered and box["visibility"] == "visible_only":
                    continue
                piece = dict(curve)
                piece["points"] = [_project3(a, box["px"], box["py"], box["pz"]),
                                   _project3(b, box["px"], box["py"], box["pz"])]
                piece["style"] = "hidden" if covered else "visible"
                resolved_curves.append(piece)
        curves = resolved_curves

    return {
        "nodes": nodes,
        "groups": groups,
        "group_node_radius": group_node_radius,
        "rings": rings,
        "lattices": lattices,
        "point_groups": point_groups,
        "centers": center_nodes,
        "boundaries": boundaries,
        "edges": sorted(edges),
        "polygons": polygons,
        "curves": curves,
    }


def _tex_for_design(design: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    plan = _resolve_model(design)
    nodes = plan["nodes"]
    groups = plan["groups"]
    edges = plan["edges"]
    boundaries = plan["boundaries"]
    centers = plan["centers"]
    polygons = plan["polygons"]
    curves = plan["curves"]
    density = _auto_density(len(nodes), len(edges), design.get("visual_density") or {})
    model = design["structure_model"]
    curve_width = float((design.get("visual_density") or {}).get("curve_line_width_pt", max(density["edge_line_width_pt"], 0.32)))
    curve_opacity = float((design.get("visual_density") or {}).get("curve_opacity", max(density["edge_opacity"], 0.52)))
    cell_outline_opacity = float((design.get("visual_density") or {}).get("cell_outline_opacity", 0.22))
    style_line = (
        r"\tikzset{"
        + f"genedge/.style={{draw=black!60,line width={density['edge_line_width_pt']:.3f}pt,opacity={density['edge_opacity']:.3f}}},"
        + f"genboundary/.style={{draw=black!60,line width={density['boundary_line_width_pt']:.3f}pt,opacity={density['boundary_opacity']:.3f}}},"
        + f"gencurve/.style={{draw=black!70,line width={curve_width:.3f}pt,opacity={curve_opacity:.3f}}},"
        + f"genhidden/.style={{draw=black!55,dashed,line width={curve_width:.3f}pt,opacity={min(curve_opacity, 0.48):.3f}}},"
        + f"gencell/.style={{draw=black!45,line width={max(density['edge_line_width_pt'] * 0.72, 0.08):.3f}pt,draw opacity={cell_outline_opacity:.3f},fill=black!12}},"
        + f"gennode/.style={{circle,fill=white,draw=black!65,line width={density['node_outline_pt']:.3f}pt,draw opacity={density['node_outline_opacity']:.3f},inner sep=0pt}}"
        + "}"
    )
    lines = [
        r"\documentclass[tikz,border=6pt]{standalone}",
        r"\begin{document}",
        r"\begin{tikzpicture}[line cap=round,line join=round]",
        "% Generated deterministically from figure.design.json structure_model.",
        style_line,
    ]
    for name, (x, y) in nodes.items():
        lines.append(f"\\coordinate ({name}) at ({x:.6f},{y:.6f});")
    for boundary in boundaries:
        lines.append(f"\\draw[genboundary] (0,0) circle[radius={boundary['radius']:.6f}cm];")
    for polygon in polygons:
        points = " -- ".join(f"({x:.6f},{y:.6f})" for x, y in polygon["points"])
        lines.append(f"\\path[gencell,fill opacity={float(polygon['fill_opacity']):.3f}] {points} -- cycle;")
    for curve in curves:
        points = " ".join(f"({x:.6f},{y:.6f})" for x, y in curve["points"])
        suffix = " -- cycle" if curve.get("closed") else ""
        style = "genhidden" if curve.get("style") == "hidden" else "gencurve"
        lines.append(f"\\draw[{style}] plot coordinates {{{points}}}{suffix};")
    for left, right in edges:
        lines.append(f"\\draw[genedge] ({left}) -- ({right});")
    for group_id, names in groups.items():
        radius = float(plan["group_node_radius"].get(group_id, 0.18))
        if radius <= 0:
            continue
        for name in names:
            lines.append(f"\\node[gennode,minimum size={2 * radius:.6f}cm] at ({name}) {{}};")
    for center_id, payload in centers.items():
        radius = payload.get("radius", 0.14)
        if type(radius) not in (int, float) or float(radius) <= 0:
            raise GenerativeError(f"center_node {center_id} radius must be positive")
        lines.append(f"\\node[gennode,minimum size={2 * float(radius):.6f}cm] at ({payload['name']}) {{}};")
    lines.extend([r"\end{tikzpicture}", r"\end{document}", ""])
    metadata = {
        "coordinate_system": model.get("coordinate_system"),
        "generator_types": [item["type"] for item in model["generators"]],
        "node_count": len(nodes),
        "edge_count": len(edges),
        "curve_count": len(curves),
        "hidden_curve_count": sum(curve.get("style") == "hidden" for curve in curves),
        "polygon_count": len(polygons),
        "resolved_density": density,
        "structure_sha256": _sha256_json(model),
    }
    return "\n".join(lines), metadata


def render_generative_design(design_path: str | Path, output: str | Path | None = None) -> tuple[Path, dict[str, Any]]:
    path = Path(design_path).resolve()
    design = validate_design(path)
    if design.get("render_mode") != "expert":
        raise GenerativeError("structure_model currently renders through Expert TikZ Mode; render_mode must be expert")
    try:
        text, metadata = _tex_for_design(design)
    except GeometryError as exc:
        raise GenerativeError(str(exc)) from exc
    basename = design["delivery"]["basename"]
    tex = Path(output).resolve() if output else path.parent / f"{basename}.tex"
    tex.write_text(text, encoding="utf-8")
    return tex, metadata


def build_generative_design(design_path: str | Path, *, engine: str = "auto") -> tuple[Path, Path, dict[str, Any]]:
    path = Path(design_path).resolve()
    design = validate_design(path)
    tex, metadata = render_generative_design(path)
    sources = list(design.get("knowledge_sources") or [])
    pdf, manifest_path = build_expert(tex, sources=sources, engine=engine)
    manifest = load_json(manifest_path)
    manifest["generation"] = metadata
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return pdf, manifest_path, metadata


def _set_path(data: dict[str, Any], path: str, value: float) -> None:
    parts = path.split(".")
    if not parts or any(not part for part in parts):
        raise GenerativeError(f"invalid search-space path: {path}")
    current: Any = data
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise GenerativeError(f"search-space path does not exist: {path}")
        current = current[part]
    if not isinstance(current, dict):
        raise GenerativeError(f"search-space path does not exist: {path}")
    current[parts[-1]] = value


def _tex_escape_label(value: str) -> str:
    return (
        value.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("$", r"\$")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def _compile_contact_sheet(root: Path, rows: list[dict[str, Any]]) -> Path:
    latexmk = shutil.which("latexmk")
    pdftoppm = shutil.which("pdftoppm")
    if not latexmk or not pdftoppm:
        raise GenerativeError("latexmk and pdftoppm are required for generative variant contact sheets")
    cells: list[str] = []
    for index, item in enumerate(rows):
        label = _tex_escape_label(", ".join(f"{key}={value}" for key, value in item["values"].items()))
        rel = Path(item["pdf"]).relative_to(root)
        cells.append(
            "\\begin{minipage}[t]{0.31\\textwidth}\\centering"
            f"\\includegraphics[width=0.96\\linewidth]{{{rel.as_posix()}}}\\\\"
            f"{{\\scriptsize v{index + 1:02d}: {label}}}\\end{{minipage}}"
        )
    sheet = [
        r"\documentclass{article}",
        r"\usepackage[margin=8mm]{geometry}",
        r"\usepackage{graphicx}",
        r"\pagestyle{empty}",
        r"\begin{document}\centering",
    ]
    for start in range(0, len(cells), 3):
        sheet.append("\\noindent " + "\\hfill ".join(cells[start : start + 3]) + "\\par\\vspace{4mm}")
    sheet.append(r"\end{document}")
    tex = root / "contact-sheet.tex"
    tex.write_text("\n".join(sheet) + "\n", encoding="utf-8")
    process = subprocess.run(
        [latexmk, "-pdf", "-interaction=nonstopmode", "-halt-on-error", tex.name],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if process.returncode:
        raise GenerativeError("contact sheet compile failed:\n" + "\n".join(process.stdout.splitlines()[-25:]))
    pdf = root / "contact-sheet.pdf"
    preview = root / "contact-sheet.png"
    _render_preview(pdf, preview, dpi=150)
    return preview


def build_generative_variants(design_path: str | Path, *, limit: int = 9, engine: str = "auto") -> tuple[Path, Path]:
    path = Path(design_path).resolve()
    design = validate_design(path)
    search_space = design.get("search_space") or []
    if not search_space:
        raise GenerativeError("generative variants require a nonempty search_space in figure.design.json")
    if limit < 1 or limit > 24:
        raise GenerativeError("variant limit must be between 1 and 24")
    axes: list[tuple[str, list[float]]] = []
    for item in search_space:
        values = item.get("values") or []
        if len(values) < 2:
            raise GenerativeError("each search_space item must have at least two values")
        axes.append((item["path"], [float(value) for value in values]))
    combinations = list(itertools.islice(itertools.product(*(values for _, values in axes)), limit))
    root = path.parent / ".funfig" / "variants"
    root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, combo in enumerate(combinations, start=1):
        variant = copy.deepcopy(design)
        value_map: dict[str, float] = {}
        for (property_path, _), value in zip(axes, combo):
            _set_path(variant, property_path, value)
            value_map[property_path] = value
        variant_dir = root / f"v{index:02d}"
        variant_dir.mkdir(parents=True, exist_ok=True)
        variant_design = variant_dir / "figure.design.json"
        write_json_atomic(variant_design, variant)
        pdf, _, metadata = build_generative_design(variant_design, engine=engine)
        rows.append({"id": f"v{index:02d}", "values": value_map, "pdf": str(pdf), "generation": metadata})
    preview = _compile_contact_sheet(root, rows)
    report = root / "variants.json"
    report.write_text(json.dumps({"variants": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return preview, report


def compare_topology_hypotheses(design_path: str | Path, reference_image: str | Path, *, limit: int = 9,
                                engine: str = "auto") -> tuple[Path, Path]:
    """Rank rendered cyclic graph rules against an aligned PNG/PGM reference."""
    if not 2 <= limit <= 24:
        raise GenerativeError("topology hypothesis limit must be between 2 and 24")
    path = Path(design_path).resolve()
    design = validate_design(path)
    generators = design.get("structure_model", {}).get("generators", [])
    rings = [item for item in generators if item["type"] == "ring_nodes"]
    if len(rings) != 1:
        raise GenerativeError("topology comparison requires exactly one ring_nodes generator")
    ring = rings[0]
    count = _require_int(ring["parameters"], "count", minimum=5)
    if count > 32:
        raise GenerativeError("topology comparison supports at most 32 ring nodes")
    topology_types = {"complete_edges", "circulant_edges", "star_polygon", "center_spokes"}
    retained = [item for item in generators if item["type"] not in topology_types]
    if any(item["type"] in {"complete_bipartite_edges", "lattice_edges", "delaunay_edges"} for item in retained):
        raise GenerativeError("topology comparison requires an isolated cyclic graph")
    centers = [item for item in retained if item["type"] == "center_node"]
    if len(centers) > 1:
        raise GenerativeError("topology comparison supports at most one center node")
    try:
        reference = normalized_ink(read_gray_image(reference_image))
    except RasterError as exc:
        raise GenerativeError(str(exc)) from exc
    candidates: list[tuple[str, list[int], bool]] = [("complete", [], False)]
    for step in range(1, count//2 + 1):
        candidates.append((f"step-{step}", [step], False))
        if step >= 2:
            candidates.append((f"ring-plus-{step}", [1, step], False))
    if centers:
        candidates = [variant for name, steps, _ in candidates
                      for variant in ((name, steps, False), (name+"-spokes", steps, True))]
    unique: list[tuple[str, list[int], bool]] = []
    seen_topologies: set[tuple[frozenset[tuple[int, int]], bool]] = set()
    for name, steps, spokes in candidates:
        if name.startswith("complete"):
            pairs = frozenset((a, b) for a in range(count) for b in range(a+1, count))
        else:
            pairs = frozenset(tuple(sorted((a, (a+step) % count))) for a in range(count) for step in steps)
        signature = (pairs, spokes)
        if signature not in seen_topologies:
            seen_topologies.add(signature)
            unique.append((name, steps, spokes))
    candidates = unique
    candidates = candidates[:limit]
    root = path.parent / ".funfig" / "hypotheses"
    root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise GenerativeError("pdftoppm is required to compare topology renderings")
    for index, (name, steps, spokes) in enumerate(candidates, 1):
        candidate = copy.deepcopy(design)
        selected = copy.deepcopy(retained)
        selected.append({"id": "hypothesis_edges", "type": "complete_edges" if name.startswith("complete") else "circulant_edges",
                         "parameters": {"nodes": ring["id"], **({} if name.startswith("complete") else {"steps": steps})}})
        if spokes:
            selected.append({"id": "hypothesis_spokes", "type": "center_spokes", "parameters": {"nodes": ring["id"], "center": centers[0]["id"]}})
        candidate["structure_model"]["generators"] = selected
        folder = root / f"h{index:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        candidate_path = folder / "figure.design.json"
        write_json_atomic(candidate_path, candidate)
        pdf, _, metadata = build_generative_design(candidate_path, engine=engine)
        ppm_root = folder / "preview"
        process = subprocess.run([pdftoppm, "-f", "1", "-singlefile", "-gray", "-scale-to", "512", str(pdf), str(ppm_root)],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if process.returncode:
            raise GenerativeError(f"pdftoppm failed for topology {name}: {process.stdout[-1000:]}")
        try:
            score = ink_distance(reference, normalized_ink(read_gray_image(ppm_root.with_suffix(".pgm"))))
        except RasterError as exc:
            raise GenerativeError(str(exc)) from exc
        rows.append({"topology": name, "score": round(score, 8), "values": {"topology": name, "score": f"{score:.4f}"},
                     "design": str(candidate_path), "pdf": str(pdf), "edge_count": metadata["edge_count"]})
    rows.sort(key=lambda row: (row["score"], row["topology"]))
    report = root / "hypotheses.json"
    report.write_text(json.dumps({"reference": str(Path(reference_image).resolve()), "score": "normalized raster mean squared error; lower is better",
                                  "scope": "single aligned cyclic graph; topology ranking is a visual hypothesis, not proof",
                                  "candidates": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    preview = _compile_contact_sheet(root, rows)
    return preview, report
