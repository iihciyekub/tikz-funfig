from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .build import BuildError, build_spec, clean_spec, doctor
from .design import validate_design
from .expert import ExpertBuildError, build_expert, inspect_expert_dependencies, mark_expert_visual_review
from .generative import (
    GenerativeError,
    build_generative_design,
    build_generative_variants,
    compare_topology_hypotheses,
    render_generative_design,
)
from .io import load_json, write_json_atomic
from .legacy import migrate_legacy_tex
from .knowledge import get_entry as get_knowledge_entry, search as search_knowledge, status as knowledge_status
from .qa import QAError, inspect_spec, mark_visual_review
from .recipes import list_recipes, load_recipe
from .render import render_spec
from .schema import load_and_validate
from .templates import get_template, list_templates, search_templates
from .theme import list_profiles, list_themes
from .optimize import optimize_spec


PUBLICATION_OFFSET_RECIPES = {
    "implicit-function",
    "function-plot",
    "data-series",
    "error-bar",
    "scatter-plot",
    "confidence-band",
    "threshold-region",
    "intersection-curves",
    "publication-threshold",
    "groupplot",
}
DEFAULT_PUBLICATION_AXIS_SHIFT = "6.5pt"
STRUCTURED_DIAGRAM_RECIPES = {
    "flowchart",
    "framework-diagram",
    "relation-diagram",
    "scientific-schematic",
    "petri-net",
}

# Product scope is deliberately narrower than technical runtime coverage. New
# recipes default to long-tail until they are explicitly promoted here.
CORE_PRODUCT_RECIPES = {
    "implicit-function",
    "function-plot",
    "data-series",
    "error-bar",
    "scatter-plot",
    "confidence-band",
    "contour-plot",
    "heatmap",
    "threshold-region",
    "intersection-curves",
    "publication-threshold",
    "groupplot",
    "mechanism-diagram",
    "flowchart",
    "framework-diagram",
    "relation-diagram",
    "scientific-schematic",
}


def _looks_like_runtime_or_skill_path(path: Path) -> bool:
    parts = path.resolve().parts
    for index in range(len(parts) - 1):
        if parts[index : index + 2] == (".agents", "skills"):
            return True
    for index in range(len(parts) - 2):
        if parts[index : index + 3] == (".codex", "plugins", "cache"):
            return True
    return False


def _assert_user_output_target(target: Path) -> None:
    if _looks_like_runtime_or_skill_path(target):
        raise ValueError(f"refusing to create user figure artifacts inside a Plugin/Skill runtime: {target}")


def _load_valid(path: str) -> tuple[Path, dict[str, Any]]:
    spec_path = Path(path).resolve()
    spec, result = load_and_validate(spec_path)
    if not result.ok:
        raise ValueError("invalid FigureSpec:\n- " + "\n- ".join(result.errors))
    return spec_path, spec


def _starter_spec(recipe_id: str, figure_id: str) -> dict[str, Any]:
    recipe = load_recipe(recipe_id)
    schema_version = "1.1" if recipe_id in STRUCTURED_DIAGRAM_RECIPES else "1.0"
    base: dict[str, Any] = {
        "schema_version": schema_version,
        "id": figure_id,
        "recipe": recipe_id,
        "kind": recipe["kind"],
        "canvas": {"width": "10cm", "height": "7cm", "border": "2pt"},
        "engine": {"latex": "auto", "compute": "none"},
        "outputs": {"basename": "figure", "formats": ["pdf"], "keep_build": False},
    }
    if schema_version == "1.1":
        base["theme"] = {"id": "journal-muted"}
        base["profile"] = {"id": "journal-single-column"}
    if recipe_id in PUBLICATION_OFFSET_RECIPES:
        base["canvas"] = {"width": "10.4cm", "height": "7.3cm", "border": "2pt"}
    if recipe["kind"] == "pgfplots":
        base.update(
            {
                "axes": {
                    "preset": (
                        "publication-offset"
                        if recipe_id in PUBLICATION_OFFSET_RECIPES
                        else "standard"
                    ),
                    "x": {
                        "label": "$x$",
                        "min": 0,
                        "max": 1,
                        "ticks": [0, 0.25, 0.5, 0.75, 1],
                    },
                    "y": {
                        "label": "$y$",
                        "min": 0,
                        "max": 1,
                        "ticks": [0, 0.25, 0.5, 0.75, 1],
                    },
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
        if recipe_id in PUBLICATION_OFFSET_RECIPES:
            base["axes"]["axis_line_shift"] = DEFAULT_PUBLICATION_AXIS_SHIFT
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
        elif recipe_id == "implicit-function":
            base["engine"]["compute"] = "gnuplot"
            base["axes"].update(
                {
                    "x": {"label": "$x$", "min": -1.5, "max": 1.5},
                    "y": {"label": "$y$", "min": -1.5, "max": 1.5},
                    "grid": "major",
                }
            )
            base["data_sources"] = [
                {
                    "id": "implicit",
                    "type": "implicit",
                    "equation": "x^2 + y^2 = 1",
                    "level": 0,
                    "samples": 100,
                    "isosamples": 100,
                }
            ]
            base["series"] = [
                {
                    "id": "implicit",
                    "source": "implicit",
                    "name_path": "implicit-curve",
                    "label": "$x^2+y^2=1$",
                    "style": {"color": "MidnightBlue", "line_width": "0.9pt"},
                }
            ]
            base["annotations"] = [
                {
                    "type": "curve_probe",
                    "series": "implicit",
                    "position": 0.15,
                    "name": "P",
                    "show": "xy",
                    "precision": 2,
                    "label_prefix": "$P=$",
                    "shift": "(5pt,6pt)",
                }
            ]
        elif recipe_id == "error-bar":
            base["data_sources"] = [
                {
                    "id": "observations",
                    "type": "coordinates",
                    "points": [[0.1, 0.2], [0.3, 0.45], [0.5, 0.4], [0.7, 0.75], [0.9, 0.82]],
                }
            ]
            base["series"] = [
                {
                    "id": "observations",
                    "source": "observations",
                    "label": "observations",
                    "style": {"mark": "*", "color": "black"},
                    "error_bars": {
                        "y": {"dir": "both", "mode": "fixed", "value": 0.08}
                    },
                }
            ]
        elif recipe_id == "scatter-plot":
            base["series"][0].update(
                {
                    "plot": "scatter",
                    "scatter": {"source": "y"},
                    "style": {"mark": "*", "mark_size": "1.8pt"},
                }
            )
        elif recipe_id == "confidence-band":
            base["data_sources"] = [
                {"id": "upper", "type": "function", "expression": "x^2+0.12", "domain": "0:1", "samples": 100},
                {"id": "lower", "type": "function", "expression": "x^2-0.12", "domain": "0:1", "samples": 100},
                {"id": "mean", "type": "function", "expression": "x^2", "domain": "0:1", "samples": 100},
            ]
            base["series"] = [
                {"id": "upper", "source": "upper", "name_path": "upper", "style": {"color": "gray", "line": "dashed"}},
                {"id": "lower", "source": "lower", "name_path": "lower", "style": {"color": "gray", "line": "dashed"}},
                {"id": "mean", "source": "mean", "label": "mean", "style": {"color": "black", "line_width": "0.9pt"}},
            ]
            base["regions"] = [
                {
                    "id": "band",
                    "type": "between",
                    "path_a": "upper",
                    "path_b": "lower",
                    "style": {"fill": "gray!35", "fill_opacity": 0.4},
                }
            ]
        elif recipe_id == "surface-plot":
            base["axes"].update(
                {
                    "z": {"label": "$f(x,y)$", "min": 0, "max": 1},
                    "view": {"azimuth": 45, "elevation": 30},
                    "box3d": "complete",
                    "colormap": "viridis",
                    "colorbar": {"position": "right", "label": "$f(x,y)$"},
                }
            )
            base["data_sources"][0].update(
                {"expression": "exp(-x^2-y^2)", "domain": "-2:2", "y_domain": "-2:2", "samples": 31}
            )
            base["series"][0]["plot"] = {"kind": "surface", "shader": "interp"}
        elif recipe_id == "contour-plot":
            base["engine"]["compute"] = "gnuplot"
            base["axes"].update(
                {
                    "view": {"azimuth": 0, "elevation": 90},
                    "colormap": "viridis",
                    "colorbar": {"position": "right", "label": "level"},
                }
            )
            base["data_sources"][0].update(
                {"expression": "x^2+y^2", "domain": "-2:2", "y_domain": "-2:2", "samples": 35}
            )
            base["series"][0]["plot"] = {"kind": "contour", "levels": [0.5, 1, 2, 3]}
        elif recipe_id == "heatmap":
            base["axes"].update(
                {"grid": "none", "colormap": "viridis", "colorbar": {"position": "right", "label": "value"}}
            )
            base["data_sources"] = [
                {"id": "matrix", "type": "coordinates", "points": [[0, 0, 0], [1, 0, 1], [0, 1, 2], [1, 1, 3]]}
            ]
            base["series"] = [
                {"id": "matrix", "source": "matrix", "plot": {"kind": "heatmap", "mesh_rows": 2, "mesh_cols": 2}}
            ]
        elif recipe_id == "quiver-field":
            base["axes"].update(
                {"z": {"min": -0.1, "max": 0.1}, "view": {"azimuth": 0, "elevation": 90}, "box3d": "complete"}
            )
            base["data_sources"][0].update(
                {"expression": "0", "domain": "-2:2", "y_domain": "-2:2", "samples": 11}
            )
            base["series"][0]["plot"] = {
                "kind": "quiver",
                "u": "-y",
                "v": "x",
                "w": "0",
                "scale_arrows": 0.16,
            }
        elif recipe_id == "groupplot":
            base["group"] = {
                "columns": 2,
                "horizontal_sep": "1.4cm",
                "vertical_sep": "1.2cm",
            }
            base["panels"] = [
                {"id": "a", "title": "(a)", "series": ["main"]},
                {"id": "b", "title": "(b)", "series": ["main"]},
            ]
    elif recipe_id == "petri-net":
        base["petri"] = {
            "places": [
                {"id": "ready", "label": "Ready", "position": {"x": 0, "y": 0}, "tokens": 1},
                {"id": "done", "label": "Done", "position": {"x": 4, "y": 0}, "tokens": 0},
            ],
            "transitions": [
                {"id": "run", "label": "Run", "position": {"x": 2, "y": 0}},
            ],
            "arcs": [
                {"from": "ready", "to": "run", "weight": 1},
                {"from": "run", "to": "done", "weight": 1},
            ],
        }
    elif recipe_id == "flowchart":
        base["diagram"] = {
            "layout": {"type": "relative"},
            "nodes": [
                {"id": "collect", "label": "Collect data", "role": "process", "position": {"type": "absolute", "x": 0, "y": 0}},
                {"id": "check", "label": "Valid?", "role": "decision", "position": {"type": "relative", "of": "collect", "direction": "right", "gap": "18mm"}},
                {"id": "analyze", "label": "Analyze", "role": "process", "position": {"type": "relative", "of": "check", "direction": "right", "gap": "18mm"}},
            ],
            "edges": [
                {"id": "e1", "from": "collect", "to": "check", "route": "straight", "arrows": "forward"},
                {"id": "e2", "from": "check", "to": "analyze", "route": "straight", "arrows": "forward", "label": "yes"},
                {"id": "e3", "from": "check", "to": "collect", "route": "curve", "routing": {"bend": -35}, "arrows": "forward", "label": "no", "label_side": "below"},
            ],
            "groups": [],
        }
    elif recipe_id == "framework-diagram":
        base["diagram"] = {
            "layout": {"type": "grid", "row_gap": "18mm", "column_gap": "28mm"},
            "nodes": [
                {"id": "input", "label": "Inputs", "role": "module", "position": {"type": "grid", "row": 0, "column": 0}},
                {"id": "mechanism", "label": "Mechanism", "role": "module", "position": {"type": "grid", "row": 0, "column": 1}},
                {"id": "outcome", "label": "Outcomes", "role": "module", "position": {"type": "grid", "row": 0, "column": 2}},
            ],
            "edges": [
                {"id": "e1", "from": "input", "to": "mechanism", "route": "straight", "arrows": "forward"},
                {"id": "e2", "from": "mechanism", "to": "outcome", "route": "straight", "arrows": "forward"},
            ],
            "groups": [{"id": "core", "members": ["input", "mechanism", "outcome"], "label": "Research framework"}],
        }
    elif recipe_id == "relation-diagram":
        base["diagram"] = {
            "layout": {"type": "relative"},
            "nodes": [
                {"id": "a", "label": "Concept A", "role": "concept", "position": {"type": "absolute", "x": 0, "y": 0}},
                {"id": "b", "label": "Concept B", "role": "concept", "position": {"type": "relative", "of": "a", "direction": "right", "gap": "24mm"}},
                {"id": "c", "label": "Concept C", "role": "concept", "position": {"type": "relative", "of": "a", "direction": "below", "gap": "18mm"}},
            ],
            "edges": [
                {"id": "e1", "from": "a", "to": "b", "route": "straight", "arrows": "both", "label": "associated"},
                {"id": "e2", "from": "a", "to": "c", "route": "straight", "arrows": "forward", "label": "supports"},
            ],
            "groups": [],
        }
    elif recipe_id == "scientific-schematic":
        base["diagram"] = {
            "layout": {"type": "manual"},
            "nodes": [
                {"id": "source", "label": "Source", "role": "component", "position": {"type": "absolute", "x": 0, "y": 0}},
                {"id": "system", "label": "System", "role": "component", "position": {"type": "absolute", "x": 3.2, "y": 0}},
                {"id": "measure", "label": "Measurement", "role": "annotation", "position": {"type": "absolute", "x": 3.2, "y": -1.8}},
            ],
            "edges": [
                {"id": "e1", "from": "source", "to": "system", "route": "straight", "arrows": "forward", "label": "input"},
                {"id": "e2", "from": "system", "to": "measure", "route": "straight", "arrows": "forward", "label": "observe", "label_side": "right"},
            ],
            "groups": [],
        }
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
    if recipe_id in {'flowchart', 'framework-diagram', 'relation-diagram'}:
        base['diagram']['layout'] = {'type': 'auto', 'direction': 'down', 'measure': True}
        for node in base['diagram']['nodes']:
            node.pop('position', None)
    elif recipe_id == 'scientific-schematic':
        base['diagram']['layout']['measure'] = True
    return base


def cmd_recipes(_: argparse.Namespace) -> int:
    for recipe in list_recipes():
        print(f"{recipe['id']:<22} {recipe['kind']:<8} {recipe['description']}")
    return 0


def cmd_kb_search(args: argparse.Namespace) -> int:
    hits = search_knowledge(args.query, limit=args.limit)
    if args.json:
        print(json.dumps([hit.__dict__ for hit in hits], indent=2, ensure_ascii=False))
        return 0
    if not hits:
        print("no knowledge matches")
        return 1
    for hit in hits:
        location = f" pages={hit.pages}" if hit.pages else ""
        print(f"{hit.kind:<6} {hit.status:<15} {hit.id}{location}")
        print(f"  {hit.title}")
        if hit.summary:
            print(f"  {hit.summary[:240].strip()}")
    return 0


def cmd_kb_show(args: argparse.Namespace) -> int:
    try:
        entry = get_knowledge_entry(args.id)
    except KeyError as exc:
        print(str(exc.args[0]), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        return 0
    print(f"{entry['kind']} {entry['id']} [{entry['status']}]")
    print(entry["title"])
    if entry.get("source"):
        print(f"source: {entry['source']}")
    if entry.get("pages"):
        print(f"location: {entry['pages']}")
    for field in ("packages", "libraries", "engine", "compile_status", "safety_flags", "skip_reason", "example_ids"):
        value = entry.get(field)
        if value:
            print(f"{field}: {', '.join(value) if isinstance(value, list) else value}")
    if entry.get("body"):
        print("\n" + entry["body"].strip())
    return 0


def cmd_kb_status(args: argparse.Namespace) -> int:
    payload = knowledge_status()
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"root: {payload['root']}")
        print(f"recipes: {payload['recipes']}")
        print(f"templates: {payload['templates']}")
        print(f"cards: {payload['cards']}")
        print(f"source examples: {payload['source_examples']}")
        print(f"manual chunks: {payload['manual_chunks']}")
        print("verification: " + ", ".join(f"{key}={value}" for key, value in payload["verification"].items()))
        print(
            "example verification: "
            + ", ".join(f"{key}={value}" for key, value in payload["example_verification"].items())
        )
    return 0


def cmd_templates_list(args: argparse.Namespace) -> int:
    items = list_templates()
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    for item in items:
        print(
            f"{item['id']:<24} {item['family']:<12} "
            f"{item['verification']:<30} {item['title']}"
        )
    return 0


def cmd_templates_search(args: argparse.Namespace) -> int:
    spec = load_json(args.spec) if args.spec else None
    items = search_templates(args.query, limit=args.limit, spec=spec)
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if not items:
        print("no template matches")
        return 1
    for item in items:
        print(f"{item['id']:<24} {item['family']:<12} {item['title']}")
        print(f"  {item['description']}")
        if spec:
            print('  fit: ' + ('eligible' if item['suitability']['eligible'] else '; '.join(item['suitability']['reasons'])))
    return 0


def cmd_templates_inspect(args: argparse.Namespace) -> int:
    print(json.dumps(get_template(args.template_id), indent=2, ensure_ascii=False))
    return 0


def cmd_capabilities(args: argparse.Namespace) -> int:
    payload = [
        {
            "id": recipe["id"],
            "kind": recipe["kind"],
            "status": recipe.get("status", "stable"),
            "product_scope": "core" if recipe["id"] in CORE_PRODUCT_RECIPES else "long_tail",
            "capabilities": recipe.get("capabilities", []),
            "knowledge_ids": recipe.get("knowledge_ids", []),
        }
        for recipe in list_recipes()
    ]
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for item in payload:
            print(
                f"{item['id']:<24} {item['status']:<10} {item['product_scope']:<10} "
                + ",".join(item["capabilities"])
            )
    return 0


def cmd_themes(args: argparse.Namespace) -> int:
    items = list_themes()
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
    else:
        for item in items:
            print(f"{item['id']:<22} {item.get('description', '')}")
    return 0


def cmd_profiles(args: argparse.Namespace) -> int:
    items = list_profiles()
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
    else:
        for item in items:
            print(
                f"{item['id']:<24} target={item.get('target_width_mm')}mm "
                f"min-text={item.get('minimum_text_pt')}pt {item.get('description', '')}"
            )
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    spec_path, spec = _load_valid(args.spec)
    qa = inspect_spec(spec, spec_path, dpi=args.dpi)
    print(f"preview: {spec_path.parent / qa['preview']}")
    print(f"machine checks: {'pass' if qa['machine_checks_passed'] else 'warnings'}")
    for warning in qa.get("warnings", []):
        print(f"warning: {warning}")
    print("visual review: pending")
    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    spec_path, spec = _load_valid(args.spec)
    if args.design:
        design_path = Path(args.design).resolve()
        design = validate_design(design_path)
        if design['id'] != spec['id'] or design['render_mode'] != 'structured':
            raise ValueError('design must refer to this structured figure')
        for key in ('target_width_mm', 'minimum_text_pt'):
            spec['diagram'].setdefault('layout', {})[key] = design['appearance'][key]
    result = optimize_spec(spec, spec_path, relayout=args.relayout,
                           max_candidates=args.candidates, repair_limit=args.repairs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['adopted'] else 1


def cmd_qa_mark(args: argparse.Namespace) -> int:
    spec_path, _ = _load_valid(args.spec)
    qa = mark_visual_review(spec_path, args.result == "pass", args.note or "")
    print(f"qa: {qa['status']}")
    return 0 if qa["status"] == "passed" else 1


def cmd_expert_build(args: argparse.Namespace) -> int:
    pdf, manifest = build_expert(
        args.tex,
        sources=args.source,
        cards=args.card,
        engine=args.engine,
        target_width_mm=args.target_width_mm,
        minimum_text_pt=args.minimum_text_pt,
    )
    print(f"pdf: {pdf}")
    print(f"manifest: {manifest}")
    print("visual QA is still required before treating the expert figure as complete")
    return 0


def cmd_expert_deps(args: argparse.Namespace) -> int:
    dependencies = inspect_expert_dependencies(args.tex)
    if args.json:
        print(json.dumps(dependencies, ensure_ascii=False, indent=2))
    else:
        document_class = dependencies.get("document_class")
        if document_class:
            status = "ok" if document_class["available"] else "missing"
            print(f"class {document_class['name']}: {status} ({document_class['file']})")
        for package in dependencies["packages"]:
            status = "ok" if package["available"] else "missing"
            print(f"package {package['name']}: {status} ({package['file']})")
        if not document_class and not dependencies["packages"]:
            print("no explicit TeX class/package dependencies found")
    return 0 if dependencies["ok"] else 1


def cmd_expert_qa(args: argparse.Namespace) -> int:
    qa = mark_expert_visual_review(args.tex, args.result == "pass", args.note or "")
    print(f"expert qa: {qa['status']}")
    return 0 if qa["status"] == "passed" else 1


def cmd_generative_render(args: argparse.Namespace) -> int:
    tex, metadata = render_generative_design(args.design, output=args.output)
    print(f"tex: {tex}")
    print(
        "generation: "
        f"nodes={metadata['node_count']} edges={metadata['edge_count']} "
        f"generators={','.join(metadata['generator_types'])}"
    )
    return 0


def cmd_generative_build(args: argparse.Namespace) -> int:
    pdf, manifest, metadata = build_generative_design(args.design, engine=args.engine)
    print(f"pdf: {pdf}")
    print(f"manifest: {manifest}")
    print(
        "generation: "
        f"nodes={metadata['node_count']} edges={metadata['edge_count']} "
        f"line={metadata['resolved_density']['edge_line_width_pt']:.3f}pt "
        f"opacity={metadata['resolved_density']['edge_opacity']:.3f}"
    )
    print("visual QA is still required before treating the generative figure as complete")
    return 0


def cmd_generative_variants(args: argparse.Namespace) -> int:
    preview, report = build_generative_variants(args.design, limit=args.limit, engine=args.engine)
    print(f"contact sheet: {preview}")
    print(f"variant report: {report}")
    print("choose a visually superior variant, transfer its parameter values to the main design, rebuild, and review")
    return 0


def cmd_generative_hypotheses(args: argparse.Namespace) -> int:
    preview, report = compare_topology_hypotheses(args.design, args.reference, limit=args.limit, engine=args.engine)
    print(f"ranked contact sheet: {preview}")
    print(f"hypothesis report: {report}")
    print("inspect the highest-ranked candidate against the reference before adopting its topology")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    _, _ = _load_valid(args.spec)
    print(f"ok: {Path(args.spec).resolve()}")
    return 0


def cmd_validate_design(args: argparse.Namespace) -> int:
    path = Path(args.design).resolve()
    validate_design(path, delivery=args.delivery)
    print(f"ok: {'delivery' if args.delivery else 'design'} {path}")
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
    if args.directory:
        target = Path(args.directory).resolve()
    elif args.project_root:
        if not args.id:
            raise ValueError("--id is required when init uses --project-root")
        target = Path(args.project_root).resolve() / "figures" / args.id
    else:
        if not args.id:
            raise ValueError("provide an output directory or --id")
        project_root = Path(os.environ.get("FUNFIG_PROJECT_ROOT", str(Path.cwd()))).resolve()
        target = project_root / "figures" / args.id
    _assert_user_output_target(target)
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

    p = sub.add_parser("kb", help="query the shared TIKZ-FunFig knowledge base")
    kb = p.add_subparsers(dest="kb_command", required=True)
    q = kb.add_parser(
        "search",
        help="search recipes, curated cards, source examples, and official manual sections with SQLite FTS5",
    )
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=8)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_kb_search)
    q = kb.add_parser("show", help="show one exact knowledge record with provenance and verification")
    q.add_argument("id")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_kb_show)
    q = kb.add_parser("status", help="show knowledge index coverage")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_kb_status)

    p = sub.add_parser("templates", help="list, search, and inspect curated academic templates")
    templates = p.add_subparsers(dest="template_command", required=True)
    q = templates.add_parser("list", help="list curated templates")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_templates_list)
    q = templates.add_parser("search", help="search curated templates")
    q.add_argument('--spec', help='rank by actual content, structural limits, and target width')
    q.add_argument("query")
    q.add_argument("--limit", type=int, default=8)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_templates_search)
    q = templates.add_parser("inspect", help="show template metadata and edit contract")
    q.add_argument("template_id")
    q.set_defaults(func=cmd_templates_inspect)

    p = sub.add_parser("capabilities", help="list Recipe capabilities and stability")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_capabilities)

    p = sub.add_parser("themes", help="list structured diagram themes")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_themes)

    p = sub.add_parser("profiles", help="list publication/output profiles")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_profiles)

    p = sub.add_parser("validate", help="validate a FigureSpec")
    p.add_argument("spec")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("validate-design", help="validate figure intent, references, and the delivery contract")
    p.add_argument("design")
    p.add_argument("--delivery", action="store_true", help="also verify artifacts, build hashes, and recorded visual QA")
    p.set_defaults(func=cmd_validate_design)

    p = sub.add_parser("render", help="render FigureSpec to deterministic .tex")
    p.add_argument("spec")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("build", help="render and compile a FigureSpec")
    p.add_argument("spec")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("inspect", help="render a PDF preview and record machine QA before visual review")
    p.add_argument("spec")
    p.add_argument("--dpi", type=int, default=180)
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser('optimize', help='measure, compare bounded layouts, repair locally, and adopt improvements')
    p.add_argument('spec')
    p.add_argument('--design', help='apply this figure design target width and minimum text baseline')
    p.add_argument('--relayout', action='store_true', help='explicitly allow movement of manual/scientific coordinates; pins still hold')
    p.add_argument('--candidates', type=int, default=3)
    p.add_argument('--repairs', type=int, default=3)
    p.set_defaults(func=cmd_optimize)

    p = sub.add_parser("qa", help="record the result of an actual visual review")
    p.add_argument("spec")
    p.add_argument("result", choices=("pass", "fail"))
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_qa_mark)

    p = sub.add_parser("expert-build", help="compile a sourced raw TikZ figure outside the stable FigureSpec capability set")
    p.add_argument("tex")
    p.add_argument("--source", action="append", default=[], help="official/manual source ID; repeat as needed")
    p.add_argument("--card", action="append", default=[], help="knowledge card ID used; repeat as needed")
    p.add_argument("--engine", choices=("auto", "pdflatex", "xelatex", "lualatex"), default="auto")
    p.add_argument('--target-width-mm', type=float)
    p.add_argument('--minimum-text-pt', type=float)
    p.set_defaults(func=cmd_expert_build)

    p = sub.add_parser("expert-deps", help="preflight document-class and package dependencies for Expert TikZ source")
    p.add_argument("tex")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_expert_deps)

    p = sub.add_parser("expert-qa", help="record an actual visual review for an Expert TikZ Mode figure")
    p.add_argument("tex")
    p.add_argument("result", choices=("pass", "fail"))
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_expert_qa)

    p = sub.add_parser("generative-render", help="render a structure_model into deterministic Expert TikZ")
    p.add_argument("design")
    p.add_argument("--output", help="optional output .tex path; defaults to delivery basename beside the design")
    p.set_defaults(func=cmd_generative_render)

    p = sub.add_parser("generative-build", help="render and compile a structure_model through sourced Expert TikZ Mode")
    p.add_argument("design")
    p.add_argument("--engine", choices=("auto", "pdflatex", "xelatex", "lualatex"), default="auto")
    p.set_defaults(func=cmd_generative_build)

    p = sub.add_parser("generative-variants", help="build a bounded parameter-search grid and contact sheet from search_space")
    p.add_argument("design")
    p.add_argument("--limit", type=int, default=9, help="maximum variant count, 1-24")
    p.add_argument("--engine", choices=("auto", "pdflatex", "xelatex", "lualatex"), default="auto")
    p.set_defaults(func=cmd_generative_variants)

    p = sub.add_parser("generative-hypotheses", help="render and rank cyclic graph topology candidates against an aligned PNG/PGM image")
    p.add_argument("design")
    p.add_argument("reference")
    p.add_argument("--limit", type=int, default=9, help="maximum hypothesis count, 2-24")
    p.add_argument("--engine", choices=("auto", "pdflatex", "xelatex", "lualatex"), default="auto")
    p.set_defaults(func=cmd_generative_hypotheses)

    p = sub.add_parser("clean", help="remove only disposable build intermediates")
    p.add_argument("spec")
    p.set_defaults(func=cmd_clean)

    p = sub.add_parser("doctor", help="check the local figure toolchain")
    p.add_argument("spec", nargs="?")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("init", help="create a starter FigureSpec directory")
    p.add_argument("directory", nargs="?")
    p.add_argument(
        "--project-root",
        help="when directory is omitted, create <project-root>/figures/<id>",
    )
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
    except (ValueError, KeyError, BuildError, QAError, ExpertBuildError, GenerativeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
