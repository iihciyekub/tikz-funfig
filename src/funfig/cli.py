from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .build import BuildError, build_spec, clean_spec, doctor
from .io import load_json, write_json_atomic
from .legacy import migrate_legacy_tex
from .recipes import list_recipes, load_recipe
from .render import render_spec
from .schema import load_and_validate


def _load_valid(path: str) -> tuple[Path, dict[str, Any]]:
    spec_path = Path(path).resolve()
    spec, result = load_and_validate(spec_path)
    if not result.ok:
        raise ValueError("invalid FigureSpec:\n- " + "\n- ".join(result.errors))
    return spec_path, spec


def _starter_spec(recipe_id: str, figure_id: str) -> dict[str, Any]:
    recipe = load_recipe(recipe_id)
    base: dict[str, Any] = {
        "schema_version": "1.0",
        "id": figure_id,
        "recipe": recipe_id,
        "kind": recipe["kind"],
        "canvas": {"width": "10cm", "height": "7cm", "border": "2pt"},
        "engine": {"latex": "auto", "compute": "none"},
        "outputs": {"basename": "figure", "keep_build": False},
    }
    if recipe["kind"] == "pgfplots":
        base.update(
            {
                "axes": {
                    "x": {"label": "$x$", "min": 0, "max": 1},
                    "y": {"label": "$y$", "min": 0, "max": 1},
                    "grid": "major",
                },
                "data_sources": [
                    {
                        "id": "main",
                        "type": "function",
                        "expression": "x^2",
                        "domain": "0:1",
                        "samples": 100,
                    }
                ],
                "series": [
                    {
                        "id": "main",
                        "source": "main",
                        "label": "$y=x^2$",
                        "style": {"color": "black", "line_width": "0.9pt"},
                    }
                ],
                "regions": [],
                "annotations": [],
                "panels": [],
            }
        )
        if recipe_id in {"threshold-region", "publication-threshold"}:
            base["regions"] = [
                {
                    "id": "regime-a",
                    "type": "rectangle",
                    "x1": 0.2,
                    "x2": 0.5,
                    "y1": 0,
                    "y2": 0.25,
                    "style": {"fill": "gray!30", "fill_opacity": 0.35},
                }
            ]
            if recipe_id == "publication-threshold":
                base["axes"].update(
                    {
                        "title": "$p=10, c=4$\\\\$B=100$",
                        "axis_line_shift": "4pt",
                        "tick_precision": 3,
                        "legend": {
                            "at": "(0.02,0.98)",
                            "anchor": "north west",
                            "font": "\\footnotesize",
                        },
                    }
                )
                base["series"][0]["name_path"] = "A"
                base["data_sources"].append(
                    {
                        "id": "other",
                        "type": "function",
                        "expression": "1-x",
                        "domain": "0:1",
                        "samples": 100,
                    }
                )
                base["series"].append(
                    {
                        "id": "other",
                        "source": "other",
                        "label": "$y=1-x$",
                        "name_path": "B",
                        "style": {"line": "dash dot", "opacity": 0.7},
                    }
                )
                base["annotations"] = [
                    {
                        "type": "intersection",
                        "path_a": "A",
                        "path_b": "B",
                        "name": "I",
                        "label": "$A=B$",
                        "shift": "(7pt,8pt)",
                        "arrow": True,
                    }
                ]
        elif recipe_id == "intersection-curves":
            base["series"][0]["name_path"] = "A"
            base["data_sources"].append(
                {"id": "other", "type": "function", "expression": "1-x", "domain": "0:1", "samples": 100}
            )
            base["series"].append(
                {"id": "other", "source": "other", "label": "$y=1-x$", "name_path": "B"}
            )
            base["annotations"] = [
                {"type": "intersection", "path_a": "A", "path_b": "B", "name": "I", "label": "$I$"}
            ]
        elif recipe_id == "groupplot":
            base["panels"] = [
                {"id": "a", "title": "(a)", "series": ["main"]},
                {"id": "b", "title": "(b)", "series": ["main"]},
            ]
    else:
        base["diagram"] = {
            "nodes": [
                {"id": "input", "label": "Input", "at": "0,0"},
                {"id": "mechanism", "label": "Mechanism", "right_of": "input"},
                {"id": "outcome", "label": "Outcome", "right_of": "mechanism"},
            ],
            "edges": [
                {"from": "input", "to": "mechanism"},
                {"from": "mechanism", "to": "outcome"},
            ],
        }
    return base


def cmd_recipes(_: argparse.Namespace) -> int:
    for recipe in list_recipes():
        print(f"{recipe['id']:<22} {recipe['kind']:<8} {recipe['description']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    _, _ = _load_valid(args.spec)
    print(f"ok: {Path(args.spec).resolve()}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    spec_path, spec = _load_valid(args.spec)
    tex_path, _ = render_spec(spec, spec_path)
    print(f"ok: {tex_path}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    spec_path, spec = _load_valid(args.spec)
    pdf_path = build_spec(spec, spec_path)
    print(f"ok: {pdf_path}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    spec_path, spec = _load_valid(args.spec)
    removed = clean_spec(spec, spec_path)
    if removed:
        for path in removed:
            print(f"removed: {path}")
    else:
        print("ok: no transient artifacts to remove")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    spec = None
    if args.spec:
        _, spec = _load_valid(args.spec)
    ok, messages = doctor(spec)
    print("\n".join(messages))
    return 0 if ok else 1


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.directory).resolve()
    target.mkdir(parents=True, exist_ok=True)
    spec_path = target / "figure.funfig.json"
    if spec_path.exists() and not args.force:
        raise ValueError(f"refusing to overwrite existing spec: {spec_path}; use --force")
    figure_id = args.id or target.name
    spec = _starter_spec(args.recipe, figure_id)
    write_json_atomic(spec_path, spec)
    print(f"ok: {spec_path}")
    return 0


def cmd_migrate_legacy(args: argparse.Namespace) -> int:
    result = migrate_legacy_tex(args.source, args.directory, args.recipe)
    print(f"ok: {result.spec_path}")
    print("detected: " + ", ".join(f"{key}={value}" for key, value in result.detected.items()))
    for warning in result.warnings:
        print(f"warning: {warning}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="funfig", description="TIKZ-FunFig figure recipe system")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("recipes", help="list available figure recipes")
    p.set_defaults(func=cmd_recipes)

    p = sub.add_parser("validate", help="validate a FigureSpec")
    p.add_argument("spec")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="render FigureSpec to deterministic .tex")
    p.add_argument("spec")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("build", help="render and compile a FigureSpec")
    p.add_argument("spec")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("clean", help="remove only disposable build intermediates")
    p.add_argument("spec")
    p.set_defaults(func=cmd_clean)

    p = sub.add_parser("doctor", help="check the local figure toolchain")
    p.add_argument("spec", nargs="?")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("init", help="create a starter FigureSpec directory")
    p.add_argument("directory")
    p.add_argument("--recipe", default="function-plot")
    p.add_argument("--id")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser(
        "migrate-legacy",
        help="create a conservative FigureSpec draft from a legacy PGFPlots .tex",
    )
    p.add_argument("source")
    p.add_argument("directory")
    p.add_argument("--recipe")
    p.set_defaults(func=cmd_migrate_legacy)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, KeyError, BuildError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

