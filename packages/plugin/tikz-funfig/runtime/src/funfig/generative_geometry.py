"""Bounded, dependency-free geometry for the generative Expert renderer."""

from __future__ import annotations

import ast
import math
from typing import Callable


class GeometryError(ValueError):
    pass


_FUNCTIONS: dict[str, Callable[..., float]] = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log, "exp": math.exp,
    "abs": abs, "floor": math.floor, "ceil": math.ceil,
}


def safe_expression(source: str) -> Callable[[float], float]:
    """Compile a numeric expression in t without Python evaluation or attributes."""
    if not isinstance(source, str) or len(source) > 240:
        raise GeometryError("expression must be a string of at most 240 characters")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise GeometryError("invalid expression syntax") from exc
    if sum(1 for _ in ast.walk(tree)) > 80:
        raise GeometryError("expression is too complex")

    def evaluate(node: ast.AST, t: float) -> float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body, t)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            result = float(node.value)
        elif isinstance(node, ast.Name) and node.id in {"t", "pi", "e"}:
            result = {"t": t, "pi": math.pi, "e": math.e}[node.id]
        elif isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            operand = evaluate(node.operand, t)
            result = operand if isinstance(node.op, ast.UAdd) else -operand
        elif isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow):
            left, right = evaluate(node.left, t), evaluate(node.right, t)
            if isinstance(node.op, ast.Add): result = left + right
            elif isinstance(node.op, ast.Sub): result = left - right
            elif isinstance(node.op, ast.Mult): result = left * right
            elif isinstance(node.op, ast.Div): result = left / right
            else:
                if abs(right) > 16 or abs(left) > 1e6:
                    raise GeometryError("expression exponent or base is too large")
                result = left ** right
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and not node.keywords and len(node.args) == 1:
            result = _FUNCTIONS[node.func.id](evaluate(node.args[0], t))
        else:
            raise GeometryError("expression uses an unsupported operation")
        if isinstance(result, complex) or not math.isfinite(result) or abs(result) > 1e6:
            raise GeometryError("expression result must be finite and within ±1e6")
        return float(result)

    # Validate syntax before returning; a forbidden branch must fail even if no sample reaches it.
    def validate(node: ast.AST) -> None:
        if isinstance(node, ast.Expression): validate(node.body)
        elif isinstance(node, ast.Constant) and type(node.value) in (int, float): pass
        elif isinstance(node, ast.Name) and node.id in {"t", "pi", "e"}: pass
        elif isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub): validate(node.operand)
        elif isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow):
            validate(node.left); validate(node.right)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and not node.keywords and len(node.args) == 1:
            validate(node.args[0])
        else: raise GeometryError("expression uses an unsupported operation")

    validate(tree)

    def sampled(t: float) -> float:
        try:
            return evaluate(tree, t)
        except (ArithmeticError, OverflowError, ValueError) as exc:
            raise GeometryError(f"expression undefined at t={t:.6g}") from exc

    return sampled


def l_system_paths(axiom: str, rules: dict[str, str], depth: int, angle_deg: float,
                   step: float, origin: tuple[float, float], heading_deg: float) -> list[list[tuple[float, float]]]:
    alphabet = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-[]")
    if not axiom or len(axiom) > 100 or set(axiom) - alphabet:
        raise GeometryError("l_system axiom must use at most 100 turtle symbols")
    if not isinstance(rules, dict) or len(rules) > 26 or any(len(key) != 1 or key not in alphabet or key in "+-[]" or not isinstance(value, str) or set(value) - alphabet for key, value in rules.items()):
        raise GeometryError("l_system rules must map single letters to turtle symbols")
    if type(depth) is not int or not 0 <= depth <= 8:
        raise GeometryError("l_system depth must be an integer from 0 to 8")
    if not all(math.isfinite(v) for v in (angle_deg, step, *origin, heading_deg)) or step <= 0:
        raise GeometryError("l_system angle, origin, heading, and positive step must be finite")
    sequence = axiom
    for _ in range(depth):
        sequence = "".join(rules.get(symbol, symbol) for symbol in sequence)
        if len(sequence) > 20000:
            raise GeometryError("l_system expansion exceeds 20000 symbols")
    x, y = origin
    heading = math.radians(heading_deg)
    turn = math.radians(angle_deg)
    stack: list[tuple[float, float, float]] = []
    paths: list[list[tuple[float, float]]] = []
    current = [(x, y)]
    segments = 0
    for symbol in sequence:
        if symbol in "FfGg":
            x += step * math.cos(heading)
            y += step * math.sin(heading)
            if max(abs(x), abs(y)) > 1e6:
                raise GeometryError("l_system coordinates exceed ±1e6")
            if symbol in "FG":
                current.append((x, y))
                segments += 1
            else:
                if len(current) > 1: paths.append(current)
                current = [(x, y)]
        elif symbol == "+": heading += turn
        elif symbol == "-": heading -= turn
        elif symbol == "[":
            if len(stack) >= 64: raise GeometryError("l_system branch nesting exceeds 64")
            stack.append((x, y, heading))
            if len(current) > 1: paths.append(current)
            current = [(x, y)]
        elif symbol == "]":
            if not stack: raise GeometryError("l_system has unmatched closing branch")
            if len(current) > 1: paths.append(current)
            x, y, heading = stack.pop()
            current = [(x, y)]
    if stack: raise GeometryError("l_system has unmatched opening branch")
    if segments > 10000: raise GeometryError("l_system draws more than 10000 segments")
    if len(current) > 1: paths.append(current)
    return paths


def delaunay_triangles(points: list[tuple[float, float]]) -> list[tuple[int, int, int]]:
    """Deterministic Bowyer-Watson triangulation for small distinct point sets."""
    if len(points) < 3 or len(points) > 128 or len(set(points)) != len(points):
        raise GeometryError("delaunay requires 3–128 distinct points")
    minx, maxx = min(x for x, _ in points), max(x for x, _ in points)
    miny, maxy = min(y for _, y in points), max(y for _, y in points)
    span = max(maxx-minx, maxy-miny)
    if span <= 1e-9: raise GeometryError("delaunay points are degenerate")
    midx, midy = (minx+maxx)/2, (miny+maxy)/2
    all_points = points + [(midx-32*span, midy-16*span), (midx, midy+32*span), (midx+32*span, midy-16*span)]
    n = len(points)
    triangles: list[tuple[int, int, int]] = [(n, n+1, n+2)]

    def circumcircle(a: int, b: int, c: int, p: int) -> bool:
        ax, ay = all_points[a][0]-all_points[p][0], all_points[a][1]-all_points[p][1]
        bx, by = all_points[b][0]-all_points[p][0], all_points[b][1]-all_points[p][1]
        cx, cy = all_points[c][0]-all_points[p][0], all_points[c][1]-all_points[p][1]
        det = (ax*ax+ay*ay)*(bx*cy-by*cx) - (bx*bx+by*by)*(ax*cy-ay*cx) + (cx*cx+cy*cy)*(ax*by-ay*bx)
        orientation = (all_points[b][0]-all_points[a][0])*(all_points[c][1]-all_points[a][1]) - (all_points[b][1]-all_points[a][1])*(all_points[c][0]-all_points[a][0])
        return det * (1 if orientation > 0 else -1) > 1e-10 * span**4

    for index in sorted(range(n), key=lambda i: (points[i][0], points[i][1])):
        bad = [tri for tri in triangles if circumcircle(*tri, index)]
        if not bad: raise GeometryError("delaunay insertion failed; check near-degenerate points")
        boundary: dict[tuple[int, int], int] = {}
        for tri in bad:
            triangles.remove(tri)
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                key = tuple(sorted((a, b)))
                boundary[key] = boundary.get(key, 0) + 1
        for (a, b), count in sorted(boundary.items()):
            if count == 1: triangles.append((a, b, index))
    result = [tuple(sorted(tri)) for tri in triangles if all(vertex < n for vertex in tri)]
    if not result: raise GeometryError("delaunay points are collinear")
    return sorted(set(result))


def voronoi_cells(points: list[tuple[float, float]], bounds: tuple[float, float, float, float]) -> list[list[tuple[float, float]]]:
    xmin, ymin, xmax, ymax = bounds
    if not all(math.isfinite(value) for value in bounds) or xmin >= xmax or ymin >= ymax:
        raise GeometryError("voronoi bounds must be [xmin,ymin,xmax,ymax] with positive area")
    if len(points) < 2 or len(points) > 128 or len(set(points)) != len(points):
        raise GeometryError("voronoi requires 2–128 distinct points")
    cells = []
    for x, y in points:
        polygon = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        for other_x, other_y in points:
            if (x, y) == (other_x, other_y): continue
            nx, ny = other_x-x, other_y-y
            threshold = (other_x*other_x+other_y*other_y-x*x-y*y)/2
            clipped: list[tuple[float, float]] = []
            for a, b in zip(polygon, polygon[1:] + polygon[:1]):
                fa, fb = a[0]*nx+a[1]*ny-threshold, b[0]*nx+b[1]*ny-threshold
                inside_a, inside_b = fa <= 1e-10, fb <= 1e-10
                if inside_a: clipped.append(a)
                if inside_a != inside_b:
                    ratio = fa/(fa-fb)
                    clipped.append((a[0]+ratio*(b[0]-a[0]), a[1]+ratio*(b[1]-a[1])))
            polygon = clipped
            if not polygon: break
        cells.append(polygon)
    return cells


def split_box_edge_occlusion(
    start: tuple[float, float, float], end: tuple[float, float, float],
    occluders: list[tuple[tuple[float, float, float], tuple[float, float, float]]],
    camera: tuple[float, float, float],
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], bool]]:
    """Split an orthographic edge where front faces of other axis-aligned boxes cover it."""
    delta = tuple(end[i]-start[i] for i in range(3))
    breakpoints = {0.0, 1.0}
    faces: list[tuple[tuple[float, float, float], tuple[float, float, float], int, float]] = []
    for origin, size in occluders:
        for axis in range(3):
            if abs(camera[axis]) < 1e-12:
                continue
            front = origin[axis] + (size[axis] if camera[axis] > 0 else 0.0)
            faces.append((origin, size, axis, front))
            lambda_0 = (front-start[axis])/camera[axis]
            lambda_slope = -delta[axis]/camera[axis]
            linear = [(lambda_0, lambda_slope, 0.0)]
            for other_axis in range(3):
                if other_axis == axis: continue
                offset = start[other_axis] + camera[other_axis]*lambda_0
                slope = delta[other_axis] + camera[other_axis]*lambda_slope
                linear.extend(((offset, slope, origin[other_axis]),
                               (offset, slope, origin[other_axis]+size[other_axis])))
            for offset, slope, boundary in linear:
                if abs(slope) > 1e-12:
                    position = (boundary-offset)/slope
                    if 1e-10 < position < 1-1e-10:
                        breakpoints.add(position)

    def hidden_at(position: float) -> bool:
        point = tuple(start[i]+position*delta[i] for i in range(3))
        for origin, size, axis, front in faces:
            travel = (front-point[axis])/camera[axis]
            if travel <= 1e-9: continue
            hit = tuple(point[i]+travel*camera[i] for i in range(3))
            if all(origin[i]-1e-9 <= hit[i] <= origin[i]+size[i]+1e-9 for i in range(3) if i != axis):
                return True
        return False

    ordered = sorted(breakpoints)
    pieces = []
    for left, right in zip(ordered, ordered[1:]):
        if right-left <= 1e-9: continue
        a = tuple(start[i]+left*delta[i] for i in range(3))
        b = tuple(start[i]+right*delta[i] for i in range(3))
        covered = hidden_at((left+right)/2)
        if pieces and pieces[-1][2] == covered:
            pieces[-1] = (pieces[-1][0], b, covered)
        else:
            pieces.append((a, b, covered))
    return pieces
