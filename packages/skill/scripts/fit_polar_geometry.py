#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _solve3(matrix: list[list[float]], vector: list[float]) -> list[float]:
    a = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(a[row][column]))
        if abs(a[pivot][column]) < 1e-12:
            raise ValueError("circle fit is singular; provide non-collinear points")
        a[column], a[pivot] = a[pivot], a[column]
        scale = a[column][column]
        a[column] = [value / scale for value in a[column]]
        for row in range(3):
            if row == column:
                continue
            factor = a[row][column]
            a[row] = [left - factor * right for left, right in zip(a[row], a[column])]
    return [a[index][3] for index in range(3)]


def fit_circle(points: list[tuple[float, float]]) -> tuple[float, float, float]:
    if len(points) < 3:
        raise ValueError("at least three points are required")
    # x^2 + y^2 + D*x + E*y + F = 0, solved by least squares.
    rows = [(x, y, 1.0) for x, y in points]
    rhs = [-(x * x + y * y) for x, y in points]
    normal = [[sum(row[i] * row[j] for row in rows) for j in range(3)] for i in range(3)]
    target = [sum(row[i] * value for row, value in zip(rows, rhs)) for i in range(3)]
    d, e, f = _solve3(normal, target)
    cx = -d / 2.0
    cy = -e / 2.0
    radius_sq = cx * cx + cy * cy - f
    if radius_sq <= 0:
        raise ValueError("circle fit produced a non-positive radius")
    return cx, cy, math.sqrt(radius_sq)


def _wrap(angle: float) -> float:
    return angle % (2.0 * math.pi)


def infer_symmetry(points: list[tuple[float, float]], cx: float, cy: float) -> dict[str, Any]:
    count = len(points)
    angles = sorted(_wrap(math.atan2(y - cy, x - cx)) for x, y in points)
    ideal = 2.0 * math.pi / count
    gaps = [
        _wrap(angles[(index + 1) % count] - angles[index])
        for index in range(count)
    ]
    mean_gap = sum(gaps) / count
    gap_rmse = math.sqrt(sum((gap - ideal) ** 2 for gap in gaps) / count)
    phase = math.degrees(angles[0])
    return {
        "order": count,
        "phase_deg": phase,
        "mean_spacing_deg": math.degrees(mean_gap),
        "ideal_spacing_deg": 360.0 / count,
        "spacing_rmse_deg": math.degrees(gap_rmse),
        "normalized_symmetry_error": gap_rmse / ideal if ideal else 0.0,
    }


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    raw_points = payload.get("points")
    if not isinstance(raw_points, list):
        raise ValueError("input JSON must contain a points array")
    points: list[tuple[float, float]] = []
    for item in raw_points:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("each point must be [x, y]")
        x, y = item
        if type(x) not in (int, float) or type(y) not in (int, float):
            raise ValueError("point coordinates must be numeric")
        points.append((float(x), float(y)))

    if "center" in payload:
        center = payload["center"]
        if not isinstance(center, (list, tuple)) or len(center) != 2:
            raise ValueError("center must be [x, y]")
        cx, cy = float(center[0]), float(center[1])
        radii = [math.hypot(x - cx, y - cy) for x, y in points]
        radius = sum(radii) / len(radii)
    else:
        cx, cy, radius = fit_circle(points)
        radii = [math.hypot(x - cx, y - cy) for x, y in points]

    radial_rmse = math.sqrt(sum((value - radius) ** 2 for value in radii) / len(radii))
    symmetry = infer_symmetry(points, cx, cy)
    return {
        "center": [cx, cy],
        "radius": radius,
        "radial_rmse": radial_rmse,
        "normalized_radial_error": radial_rmse / radius if radius else 0.0,
        "node_count": len(points),
        "symmetry": symmetry,
        "suggested_structure_model": {
            "coordinate_system": "polar",
            "symmetry": {
                "group": f"C{len(points)}",
                "order": len(points),
                "phase_deg": symmetry["phase_deg"],
                "tolerance": max(symmetry["normalized_symmetry_error"], radial_rmse / radius if radius else 0.0),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fit a circle and cyclic symmetry to detected ring-node centers")
    parser.add_argument("input", type=Path, help="JSON containing points: [[x,y], ...] and optional center")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"ok: {args.output}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
