from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from funfig import __version__
from funfig.build import build_spec, clean_spec
from funfig.cli import CORE_PRODUCT_RECIPES, main as cli_main
from funfig.io import load_json, write_json_atomic
from funfig.legacy import migrate_legacy_tex
from funfig.paths import PROJECT_ROOT
from funfig.qa import inspect_spec, mark_visual_review
from funfig.recipes import recipe_ids
from funfig.render import render_spec
from funfig.schema import validate_spec
from funfig.templates import get_template, list_templates, search_templates


GOLDEN_CASES = ("fig1", "fig4", "fig11")
SCIENTIFIC_GOLDEN_CASES = ("error-bar", "scatter-plot", "confidence-band", "groupplot")
ADVANCED_GOLDEN_CASES = ("surface-plot", "contour-plot", "heatmap", "quiver-field")
METHOD_GOLDEN_CASES = ("implicit-function",)
DIAGRAM_GOLDEN_CASES = (
    "flowchart-decision",
    "flowchart-sloped-labels",
    "flowchart-feedback",
    "framework-grouped",
    "framework-layered",
    "relations-labelled",
    "schematic-scientific",
    "diagram-longtext-cjk",
)


class FunFigCoreTests(unittest.TestCase):
    def test_product_scope_whitelist_keeps_common_paper_figures_core(self) -> None:
        required_core = {
            "function-plot", "data-series", "error-bar", "scatter-plot",
            "confidence-band", "publication-threshold", "groupplot",
            "flowchart", "framework-diagram", "relation-diagram",
        }
        self.assertTrue(required_core <= CORE_PRODUCT_RECIPES)
        self.assertNotIn("surface-plot", CORE_PRODUCT_RECIPES)
        self.assertNotIn("quiver-field", CORE_PRODUCT_RECIPES)
        self.assertNotIn("petri-net", CORE_PRODUCT_RECIPES)

    def test_portable_plugin_bundle_matches_source(self) -> None:
        plugin = PROJECT_ROOT / "packages/plugin/tikz-funfig"
        manifest = load_json(plugin / "plugin.json")
        self.assertEqual(manifest["version"], __version__)

        self.assertEqual(
            (PROJECT_ROOT / "packages/skill/SKILL.md").read_text(encoding="utf-8"),
            (plugin / "skills/TIKZ-FunFig/SKILL.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (PROJECT_ROOT / "packages/skill/references/methods.md").read_text(encoding="utf-8"),
            (plugin / "skills/TIKZ-FunFig/references/methods.md").read_text(encoding="utf-8"),
        )
        for schema_name in (
            "figure-spec.schema.json",
            "source-example.schema.json",
            "template.schema.json",
        ):
            self.assertEqual(
                (PROJECT_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"),
                (plugin / "runtime/schemas" / schema_name).read_text(encoding="utf-8"),
            )

        source_recipes = sorted(path.name for path in (PROJECT_ROOT / "recipes").glob("*.json"))
        plugin_recipes = sorted(path.name for path in (plugin / "runtime/recipes").glob("*.json"))
        self.assertEqual(source_recipes, plugin_recipes)
        for name in source_recipes:
            self.assertEqual(
                (PROJECT_ROOT / "recipes" / name).read_text(encoding="utf-8"),
                (plugin / "runtime/recipes" / name).read_text(encoding="utf-8"),
            )

        source_modules = sorted(path.name for path in (PROJECT_ROOT / "src/funfig").glob("*.py"))
        plugin_modules = sorted(path.name for path in (plugin / "runtime/src/funfig").glob("*.py"))
        self.assertEqual(source_modules, plugin_modules)
        for name in source_modules:
            self.assertEqual(
                (PROJECT_ROOT / "src/funfig" / name).read_text(encoding="utf-8"),
                (plugin / "runtime/src/funfig" / name).read_text(encoding="utf-8"),
            )

        for directory in ("themes", "profiles"):
            source_files = sorted(path.name for path in (PROJECT_ROOT / directory).glob("*.json"))
            plugin_files = sorted(path.name for path in (plugin / "runtime" / directory).glob("*.json"))
            self.assertEqual(source_files, plugin_files)
            for name in source_files:
                self.assertEqual(
                    (PROJECT_ROOT / directory / name).read_text(encoding="utf-8"),
                    (plugin / "runtime" / directory / name).read_text(encoding="utf-8"),
                )

        skills_manifest = load_json(PROJECT_ROOT / "packages/skills/index.json")
        expected_skills = {"TIKZ-FunFig", *(item["skill_id"] for item in skills_manifest["skills"])}
        actual_skills = {
            path.name for path in (plugin / "skills").iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(actual_skills, expected_skills)
        for item in skills_manifest["skills"]:
            source = PROJECT_ROOT / item["source_dir"] / "SKILL.md"
            bundled = plugin / "skills" / item["skill_id"] / "SKILL.md"
            self.assertEqual(source.read_text(encoding="utf-8"), bundled.read_text(encoding="utf-8"))
            self.assertTrue((plugin / "skills" / item["skill_id"] / "scripts/funfig.sh").is_file())

        for relative in (
            "aliases.json",
            "cards/index.json",
            "examples/index.json",
            "corpus/index.json",
            "corpus/sources.json",
            "corpus/examples.jsonl",
            "corpus/pgfplots-1.18.2.jsonl",
            "corpus/pgfplots-1.18.2.index.json",
            "manual-index/pgfmanual-3.1.11a.jsonl",
            "manual-index/pgfmanual-3.1.11a.libraries.json",
        ):
            self.assertEqual(
                (PROJECT_ROOT / "knowledge" / relative).read_text(encoding="utf-8"),
                (plugin / "knowledge" / relative).read_text(encoding="utf-8"),
            )

        source_templates = PROJECT_ROOT / "examples/templates"
        plugin_templates = plugin / "runtime/templates"
        source_files = sorted(
            path.relative_to(source_templates)
            for path in source_templates.rglob("*")
            if path.is_file()
        )
        plugin_files = sorted(
            path.relative_to(plugin_templates)
            for path in plugin_templates.rglob("*")
            if path.is_file()
        )
        self.assertEqual(source_files, plugin_files)
        for relative in source_files:
            self.assertEqual(
                (source_templates / relative).read_bytes(),
                (plugin_templates / relative).read_bytes(),
            )

        self.assertEqual(
            (PROJECT_ROOT / "IconKitchen/macos/AppIcon128.png").read_bytes(),
            (plugin / "assets/icon.png").read_bytes(),
        )
        self.assertEqual(
            (PROJECT_ROOT / "IconKitchen/macos/AppIcon512.png").read_bytes(),
            (plugin / "assets/logo.png").read_bytes(),
        )

    def test_recipe_registry(self) -> None:
        self.assertEqual(
            recipe_ids(),
            [
                "implicit-function",
                "function-plot",
                "data-series",
                "error-bar",
                "scatter-plot",
                "confidence-band",
                "surface-plot",
                "contour-plot",
                "heatmap",
                "quiver-field",
                "threshold-region",
                "intersection-curves",
                "publication-threshold",
                "groupplot",
                "mechanism-diagram",
                "flowchart",
                "framework-diagram",
                "relation-diagram",
                "petri-net",
                "scientific-schematic",
            ],
        )

    def test_recipe_reference_examples_resolve(self) -> None:
        for recipe_id in recipe_ids():
            recipe = load_json(PROJECT_ROOT / "recipes" / f"{recipe_id}.recipe.json")
            for reference in recipe.get("reference_examples", []):
                with self.subTest(recipe=recipe_id, reference=reference):
                    self.assertTrue(
                        (PROJECT_ROOT / reference).exists(),
                        f"missing recipe reference: {reference}",
                    )

    def test_plot_recipes_use_curated_knowledge_not_legacy_examples(self) -> None:
        card_ids = {
            item["id"]
            for item in load_json(PROJECT_ROOT / "knowledge/cards/index.json")["cards"]
        }
        plot_recipes = {
            "implicit-function",
            "function-plot",
            "data-series",
            "error-bar",
            "scatter-plot",
            "confidence-band",
            "surface-plot",
            "contour-plot",
            "heatmap",
            "quiver-field",
            "threshold-region",
            "intersection-curves",
            "publication-threshold",
            "groupplot",
        }
        for recipe_id in sorted(plot_recipes):
            recipe = load_json(PROJECT_ROOT / "recipes" / f"{recipe_id}.recipe.json")
            with self.subTest(recipe=recipe_id):
                self.assertNotIn("reference_examples", recipe)
                knowledge_ids = recipe.get("knowledge_ids", [])
                self.assertTrue(knowledge_ids)
                self.assertTrue(set(knowledge_ids).issubset(card_ids))

    def test_legacy_method_catalog_tracks_promoted_helpers(self) -> None:
        catalog = load_json(PROJECT_ROOT / "references/methods/legacy-methods.json")
        methods = catalog["methods"]
        promoted = {
            item["semantic_method"]
            for item in methods
            if item.get("status") == "promoted"
        }
        self.assertTrue(
            {
                "implicit-contour",
                "coordinate-value",
                "curve-probe",
                "curve-label",
                "named-intersection",
                "multi-intersection",
                "fill-between",
                "coordinate-template",
                "spy-detail",
            }.issubset(promoted)
        )

    def test_implicit_method_golden_renders_promoted_semantics(self) -> None:
        path = PROJECT_ROOT / "examples/golden/implicit-function/figure.funfig.json"
        spec = load_json(path)
        result = validate_spec(spec, path)
        self.assertTrue(result.ok, result.errors)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, spec)
            tex_path, manifest = render_spec(spec, spec_path)
            tex = tex_path.read_text(encoding="utf-8")
            self.assertIn("set xrange [-1.4:1.4];", tex)
            self.assertIn("set yrange [-1.4:1.4];", tex)
            self.assertIn("set cntrparam levels discrete 0;", tex)
            self.assertIn("splot (x**2 + y**2)-(1);", tex)
            self.assertIn("coordinate[pos=0.12] (P)", tex)
            self.assertIn("node[pos=0.72,fill=white", tex)
            self.assertIn("fill opacity=0.94", tex)
            self.assertIn("text opacity=1", tex)
            self.assertIn("rounded corners=1pt", tex)
            self.assertIn("sloped,font=\\scriptsize] {$y=x$}", tex)
            self.assertIn("\\funfigcoordx{P}{2}", tex)
            self.assertIn("\\funfigcoordy{P}{2}", tex)
            self.assertIn(
                "name intersections={of=circle-path and diagonal-path,by={I1,I2}}",
                tex,
            )
            self.assertIn("\\funfigcoordx{I1}{3}", tex)
            self.assertIn("\\funfigcoordy{I2}{3}", tex)
            self.assertIn("\\usetikzlibrary{spy}", tex)
            self.assertIn("\\spy[circle,magnification=3.2,size=1.4cm,connect spies", tex)
            self.assertTrue(manifest["dependencies"]["gnuplot"])
            self.assertTrue(manifest["dependencies"]["shell_escape"])

    def test_legacy_reference_policy_excludes_generated_artifacts(self) -> None:
        legacy = PROJECT_ROOT / "references/legacy"
        publication = legacy / "publication-sustainability-1485080"
        self.assertTrue((legacy / "tikz-memo").is_dir())
        self.assertTrue((legacy / "pgfplots-memo").is_dir())
        self.assertTrue(publication.is_dir())
        self.assertEqual(len(list(publication.glob("fig*/generate_data_legacy.py"))), 11)
        forbidden = ("*.ipynb", "*.pdf", "*.svg", "*.ttf", "*.otf")
        for pattern in forbidden:
            self.assertFalse(list(legacy.rglob(pattern)), f"legacy artifact returned: {pattern}")

    def test_portable_plugin_excludes_raw_reference_and_source_material(self) -> None:
        plugin = PROJECT_ROOT / "packages/plugin/tikz-funfig"
        self.assertFalse((plugin / "references").exists())
        self.assertFalse((plugin / "runtime/references").exists())
        self.assertFalse((plugin / "sources").exists())
        self.assertFalse((plugin / "runtime/sources").exists())

    def test_basic_example_validates(self) -> None:
        path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        spec = load_json(path)
        result = validate_spec(spec, path)
        self.assertTrue(result.ok, result.errors)

    def test_callout_marker_and_label_styles_are_independent(self) -> None:
        spec = load_json(PROJECT_ROOT / "examples/basic-function/figure.funfig.json")
        spec["series"][0]["name_path"] = "A"
        spec["data_sources"].append({"id": "line", "type": "function", "expression": "1-x"})
        spec["series"].append({"id": "line", "source": "line", "name_path": "B"})
        for kind in ("point", "intersection"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                annotation = {
                    "type": kind, "label": "callout", "arrow": True,
                    "style": {"fill": "red", "draw": "blue", "color": "green"},
                }
                annotation.update({"at": [0.5, 0.25]} if kind == "point" else {
                    "path_a": "A", "path_b": "B", "name": "crossing",
                })
                spec["annotations"] = [annotation]
                path = Path(temp) / "figure.funfig.json"
                write_json_atomic(path, spec)
                tex_path, _ = render_spec(spec, path)
                tex = tex_path.read_text()
                label = next(line for line in tex.splitlines() if line.startswith("\\node[") and "{callout}" in line)
                self.assertIn("text=green", label)
                self.assertIn("fill=white", label)
                self.assertNotIn("fill=red", label)
                self.assertNotIn("draw=blue", label)
                self.assertIn("fill=red", tex)
                annotation["label_style"] = {"fill": "yellow", "color": "black", "fill_opacity": 0.5}
                annotation["arrow_anchor"] = "east"
                write_json_atomic(path, spec)
                tex_path, _ = render_spec(spec, path)
                tex = tex_path.read_text()
                label = next(line for line in tex.splitlines() if line.startswith("\\node[") and "{callout}" in line)
                self.assertIn("fill=yellow", label)
                self.assertIn("text=black", label)
                self.assertIn("fill opacity=0.5", label)
                self.assertNotIn("text=green", label)
                connector = next(line for line in tex.splitlines() if ".east) --" in line)
                self.assertLess(tex.index(label), tex.index(connector))
                self.assertTrue(build_spec(spec, path).is_file())

    def test_default_point_connector_is_behind_its_label(self) -> None:
        spec = load_json(PROJECT_ROOT / "examples/basic-function/figure.funfig.json")
        spec["annotations"][0]["arrow"] = True
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "figure.funfig.json"
            write_json_atomic(path, spec)
            tex_path, _ = render_spec(spec, path)
            tex = tex_path.read_text()
            arrow = next(line for line in tex.splitlines() if line.startswith("\\draw[") and " -- " in line)
            label = next(line for line in tex.splitlines() if line.startswith("\\node["))
            self.assertLess(tex.index(arrow), tex.index(label))
            self.assertIn("draw=gray!65", arrow)
            self.assertTrue(build_spec(spec, path).is_file())

    def test_label_style_rejects_invalid_or_unsupported_input(self) -> None:
        spec = load_json(PROJECT_ROOT / "examples/basic-function/figure.funfig.json")
        for kind, style in (("point", "red"), ("label", {"color": "red"})):
            with self.subTest(kind=kind):
                spec["annotations"] = [{"type": kind, "at": [0, 0], "label": "x", "label_style": style}]
                result = validate_spec(spec)
                self.assertFalse(result.ok)
                self.assertTrue(any("label_style" in message for message in result.errors))

    def test_publication_offset_is_default_for_ordinary_2d_recipes(self) -> None:
        source_path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        source = load_json(source_path)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            tex_path, _ = render_spec(source, spec_path)
            rendered = tex_path.read_text(encoding="utf-8")
            self.assertIn("axis line shift=6.5pt", rendered)
            self.assertIn("tick align=inside", rendered)
            self.assertIn("major tick length=2.2pt", rendered)
            self.assertIn("axis line style={line width=0.45pt}", rendered)
            self.assertIn("tick style={black,line width=0.4pt}", rendered)
            self.assertIn("enlargelimits=false", rendered)
            self.assertIn("extra y ticks={0,1}", rendered)

            source["annotations"] = [
                {"type": "label", "at": [0.5, 0.5], "label": "note"}
            ]
            write_json_atomic(spec_path, source)
            tex_path, _ = render_spec(source, spec_path)
            rendered = tex_path.read_text(encoding="utf-8")
            self.assertIn("fill=white", rendered)
            self.assertIn("fill opacity=0.94", rendered)
            self.assertIn("text opacity=1", rendered)
            self.assertIn("rounded corners=1pt", rendered)

            source["axes"]["preset"] = "standard"
            write_json_atomic(spec_path, source)
            tex_path, _ = render_spec(source, spec_path)
            self.assertNotIn("axis line shift=", tex_path.read_text(encoding="utf-8"))

            source["axes"]["axis_line_shift"] = "9pt"
            write_json_atomic(spec_path, source)
            tex_path, _ = render_spec(source, spec_path)
            self.assertIn("axis line shift=9pt", tex_path.read_text(encoding="utf-8"))

    def test_project_root_init_uses_figures_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project_root = Path(temp) / "paper"
            result = cli_main(
                [
                    "init",
                    "--project-root",
                    str(project_root),
                    "--id",
                    "fig-demand",
                    "--recipe",
                    "publication-threshold",
                ]
            )
            self.assertEqual(result, 0)
            spec_path = project_root / "figures" / "fig-demand" / "figure.funfig.json"
            self.assertTrue(spec_path.exists())
            spec = load_json(spec_path)
            self.assertEqual(spec["axes"]["preset"], "publication-offset")
            self.assertEqual(spec["axes"]["axis_line_shift"], "6.5pt")
            self.assertEqual(spec["canvas"]["width"], "10.4cm")
            self.assertEqual(spec["canvas"]["height"], "7.3cm")
            self.assertEqual(spec["axes"]["x"]["ticks"][0], spec["axes"]["x"]["min"])
            self.assertEqual(spec["axes"]["x"]["ticks"][-1], spec["axes"]["x"]["max"])
            self.assertEqual(spec["axes"]["y"]["ticks"][0], spec["axes"]["y"]["min"])
            self.assertEqual(spec["axes"]["y"]["ticks"][-1], spec["axes"]["y"]["max"])

    def test_init_without_directory_uses_current_project_figures(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project_root = Path(temp)
            previous = Path.cwd()
            try:
                os.chdir(project_root)
                result = cli_main(["init", "--id", "fig-auto", "--recipe", "function-plot"])
            finally:
                os.chdir(previous)
            self.assertEqual(result, 0)
            spec_path = project_root / "figures" / "fig-auto" / "figure.funfig.json"
            self.assertTrue(spec_path.is_file())
            self.assertEqual(load_json(spec_path)["outputs"]["formats"], ["pdf"])

    def test_init_uses_funfig_project_root_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project_root = Path(temp) / "paper"
            previous = os.environ.get("FUNFIG_PROJECT_ROOT")
            os.environ["FUNFIG_PROJECT_ROOT"] = str(project_root)
            try:
                result = cli_main(["init", "--id", "fig-env"])
            finally:
                if previous is None:
                    os.environ.pop("FUNFIG_PROJECT_ROOT", None)
                else:
                    os.environ["FUNFIG_PROJECT_ROOT"] = previous
            self.assertEqual(result, 0)
            self.assertTrue((project_root / "figures" / "fig-env" / "figure.funfig.json").is_file())

    def test_init_refuses_plugin_or_skill_runtime_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / ".agents" / "skills" / "TIKZ-FunFig" / "figures" / "bad"
            result = cli_main(["init", str(target), "--id", "bad"])
            self.assertEqual(result, 2)
            self.assertFalse((target / "figure.funfig.json").exists())

    def test_explicit_init_directory_wins_over_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            explicit = root / "custom-figure"
            project_root = root / "paper"
            result = cli_main(
                [
                    "init",
                    str(explicit),
                    "--project-root",
                    str(project_root),
                    "--id",
                    "fig-explicit",
                ]
            )
            self.assertEqual(result, 0)
            self.assertTrue((explicit / "figure.funfig.json").is_file())
            self.assertFalse((project_root / "figures" / "fig-explicit").exists())

    def test_svg_output_contract_requires_pdf_and_accepts_pdf_svg(self) -> None:
        path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        spec = load_json(path)
        spec["outputs"] = {"basename": "figure", "formats": ["svg"], "keep_build": False}
        invalid = validate_spec(spec, path)
        self.assertFalse(invalid.ok)
        self.assertTrue(any("must include pdf" in error for error in invalid.errors))

        spec["outputs"]["formats"] = ["pdf", "svg"]
        valid = validate_spec(spec, path)
        self.assertTrue(valid.ok, valid.errors)

    def test_svg_output_is_generated_and_recorded(self) -> None:
        source = load_json(PROJECT_ROOT / "examples/basic-function/figure.funfig.json")
        source["outputs"] = {"basename": "figure", "formats": ["pdf", "svg"], "keep_build": False}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            pdf_path = build_spec(source, spec_path)
            svg_path = root / "figure.svg"
            self.assertTrue(pdf_path.is_file())
            self.assertTrue(svg_path.is_file())
            self.assertGreater(svg_path.stat().st_size, 100)
            manifest = load_json(root / ".funfig/manifest.json")
            self.assertEqual(manifest["artifacts"]["svg"], "figure.svg")
            self.assertIn("svg_sha256", manifest["hashes"])
            self.assertFalse((root / ".funfig/build").exists())

    def test_invalid_axis_preset_is_rejected(self) -> None:
        source_path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        source = load_json(source_path)
        source["axes"]["preset"] = "mystery"
        result = validate_spec(source, source_path)
        self.assertFalse(result.ok)
        self.assertTrue(any("axes.preset" in error for error in result.errors))

    def test_publication_threshold_example_validates(self) -> None:
        path = PROJECT_ROOT / "examples/publication-threshold/figure.funfig.json"
        spec = load_json(path)
        result = validate_spec(spec, path)
        self.assertTrue(result.ok, result.errors)

    def test_publication_goldens_validate(self) -> None:
        for case in GOLDEN_CASES:
            with self.subTest(case=case):
                path = PROJECT_ROOT / f"examples/golden/{case}/figure.funfig.json"
                spec = load_json(path)
                result = validate_spec(spec, path)
                self.assertTrue(result.ok, result.errors)
                self.assertTrue(spec["metadata"]["golden"])

    def test_publication_goldens_match_committed_tex(self) -> None:
        for case in GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                tex_path, _ = render_spec(spec, spec_path)
                expected_tex = source_dir / f"{case}.tex"
                self.assertEqual(
                    tex_path.read_text(encoding="utf-8"),
                    expected_tex.read_text(encoding="utf-8"),
                )
                tex = tex_path.read_text(encoding="utf-8")
                self.assertIn("mark=none", tex)
                if case == "fig4":
                    self.assertIn("name intersections={of=A and C,by=profit-zero}", tex)

    def test_scientific_goldens_validate(self) -> None:
        for case in SCIENTIFIC_GOLDEN_CASES:
            with self.subTest(case=case):
                path = PROJECT_ROOT / f"examples/golden/{case}/figure.funfig.json"
                spec = load_json(path)
                result = validate_spec(spec, path)
                self.assertTrue(result.ok, result.errors)
                self.assertTrue(spec["metadata"]["golden"])

    def test_scientific_goldens_match_committed_tex(self) -> None:
        required_fragments = {
            "error-bar": ("error bars/.cd", "x error plus=xerr_plus", "y error minus=yerr_minus"),
            "scatter-plot": ("scatter src=explicit", "meta=score", "colorbar style={ylabel={score}}"),
            "confidence-band": ("name path=upper", "fill between [of=upper and lower]"),
            "groupplot": ("group size=2 by 2", "xlabels at={edge bottom}", "ylabels at={edge left}"),
        }
        for case in SCIENTIFIC_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                expected_tex = source_dir / f"{case}.tex"
                expected = expected_tex.read_text(encoding="utf-8")
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig", f"{case}.tex"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                tex_path, _ = render_spec(spec, spec_path)
                actual = tex_path.read_text(encoding="utf-8")
                self.assertEqual(actual, expected)
                for fragment in required_fragments[case]:
                    self.assertIn(fragment, actual)

    def test_structured_diagram_goldens_validate(self) -> None:
        for case in DIAGRAM_GOLDEN_CASES:
            with self.subTest(case=case):
                path = PROJECT_ROOT / f"examples/golden/{case}/figure.funfig.json"
                spec = load_json(path)
                result = validate_spec(spec, path)
                self.assertTrue(result.ok, result.errors)
                self.assertEqual(spec["schema_version"], "1.1")
                self.assertTrue(spec["metadata"]["golden"])

    def test_structured_diagram_goldens_match_committed_tex(self) -> None:
        required_fragments = {
            "flowchart-decision": ("diamond,aspect=2", "{yes}", "{no}"),
            "flowchart-sloped-labels": ("above,sloped", "below,sloped", "{first path}", "{second path}"),
            "flowchart-feedback": ("bend left=50", "(check.south)", "(collect.south)"),
            "framework-grouped": ("on background layer", "fit=(x1)(x2)", "-|"),
            "framework-layered": ("fit=(input)(process)(outcome)", "fit=(core)(moderator)"),
            "relations-labelled": ("[<->", "bend left=22", "loop below"),
            "schematic-scientific": ("Stimulus $S$", "fit=(system)(sensor)"),
            "diagram-longtext-cjk": ("\\usepackage[UTF8]{ctex}", "参数 \\#1", "95\\%"),
        }
        for case in DIAGRAM_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                expected_tex = source_dir / f"{case}.tex"
                expected = expected_tex.read_text(encoding="utf-8")
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig", f"{case}.tex"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                tex_path, manifest = render_spec(spec, spec_path)
                actual = tex_path.read_text(encoding="utf-8")
                self.assertEqual(actual, expected)
                self.assertEqual(manifest["mode"], "structured")
                self.assertEqual(manifest["qa"]["status"], "not_checked")
                for fragment in required_fragments[case]:
                    self.assertIn(fragment, actual)

    def test_structured_diagram_rejects_position_and_group_cycles(self) -> None:
        path = PROJECT_ROOT / "examples/golden/flowchart-feedback/figure.funfig.json"
        spec = load_json(path)
        spec["diagram"]["nodes"][0]["position"] = {
            "type": "relative", "of": "check", "direction": "left", "gap": "18mm"
        }
        result = validate_spec(spec, path)
        self.assertFalse(result.ok)
        self.assertTrue(any("dependencies" in error or "absolute root" in error for error in result.errors))

        grouped_path = PROJECT_ROOT / "examples/golden/framework-layered/figure.funfig.json"
        grouped = load_json(grouped_path)
        grouped["diagram"]["groups"][0]["members"] = ["system"]
        result = validate_spec(grouped, grouped_path)
        self.assertFalse(result.ok)
        self.assertTrue(any("containment" in error for error in result.errors))

    def test_structured_diagram_rejects_invalid_self_loop_and_duplicate_grid_cell(self) -> None:
        path = PROJECT_ROOT / "examples/golden/relations-labelled/figure.funfig.json"
        spec = load_json(path)
        spec["diagram"]["edges"][3]["route"] = "straight"
        result = validate_spec(spec, path)
        self.assertFalse(result.ok)
        self.assertTrue(any("self-edge" in error for error in result.errors))

        grid_path = PROJECT_ROOT / "examples/golden/flowchart-decision/figure.funfig.json"
        grid = load_json(grid_path)
        grid["diagram"]["nodes"][1]["position"] = {"type": "grid", "row": 0, "column": 0}
        result = validate_spec(grid, grid_path)
        self.assertFalse(result.ok)
        self.assertTrue(any("duplicates grid cell" in error for error in result.errors))

    def test_structured_recipe_requires_schema_11_and_allowed_roles(self) -> None:
        path = PROJECT_ROOT / "examples/golden/flowchart-decision/figure.funfig.json"
        spec = load_json(path)
        spec["schema_version"] = "1.0"
        spec.pop("theme", None)
        spec.pop("profile", None)
        result = validate_spec(spec, path)
        self.assertFalse(result.ok)
        self.assertTrue(any("requires schema_version" in error for error in result.errors))

        spec = load_json(path)
        spec["diagram"]["nodes"][0]["role"] = "concept"
        result = validate_spec(spec, path)
        self.assertFalse(result.ok)
        self.assertTrue(any("is not allowed by recipe" in error for error in result.errors))

    def test_advanced_goldens_validate(self) -> None:
        for case in ADVANCED_GOLDEN_CASES:
            with self.subTest(case=case):
                path = PROJECT_ROOT / f"examples/golden/{case}/figure.funfig.json"
                spec = load_json(path)
                result = validate_spec(spec, path)
                self.assertTrue(result.ok, result.errors)
                self.assertTrue(spec["metadata"]["golden"])

    def test_advanced_goldens_match_committed_tex(self) -> None:
        required_fragments = {
            "surface-plot": ("surf", "shader=interp", "view={45}{30}"),
            "contour-plot": ("contour gnuplot", "levels={0.5,1,2,3}"),
            "heatmap": ("matrix plot*", "point meta=explicit", "mesh/rows=3"),
            "quiver-field": ("quiver={", "u={-y}", "v={x}"),
        }
        for case in ADVANCED_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                expected_tex = source_dir / f"{case}.tex"
                expected = expected_tex.read_text(encoding="utf-8")
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig", f"{case}.tex"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                tex_path, _ = render_spec(spec, spec_path)
                actual = tex_path.read_text(encoding="utf-8")
                self.assertEqual(actual, expected)
                for fragment in required_fragments[case]:
                    self.assertIn(fragment, actual)

    def test_method_goldens_match_committed_tex(self) -> None:
        required_fragments = {
            "implicit-function": (
                "raw gnuplot",
                "set cntrparam levels discrete 0;",
                "coordinate[pos=0.12] (P)",
                "node[pos=0.72,fill=white",
                "rounded corners=1pt",
                "sloped,font=\\scriptsize] {$y=x$}",
                "\\funfigcoordx{P}{2}",
                "\\funfigcoordy{P}{2}",
                "name intersections={of=circle-path and diagonal-path,by={I1,I2}}",
                "\\funfigcoordx{I1}{3}",
                "\\funfigcoordy{I2}{3}",
                "\\usetikzlibrary{spy}",
                "\\spy[circle,magnification=3.2,size=1.4cm,connect spies",
            )
        }
        for case in METHOD_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                expected_tex = source_dir / f"{case}.tex"
                expected = expected_tex.read_text(encoding="utf-8")
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig", f"{case}.tex"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                tex_path, _ = render_spec(spec, spec_path)
                actual = tex_path.read_text(encoding="utf-8")
                self.assertEqual(actual, expected)
                for fragment in required_fragments[case]:
                    self.assertIn(fragment, actual)

    def test_fig4_legacy_migration_produces_valid_draft(self) -> None:
        source = PROJECT_ROOT / "references/legacy/publication-sustainability-1485080/fig4/fig4.tex"
        with tempfile.TemporaryDirectory() as temp:
            result = migrate_legacy_tex(source, temp)
            spec = load_json(result.spec_path)
            validation = validate_spec(spec, result.spec_path)
            self.assertTrue(validation.ok, validation.errors)
            self.assertEqual(spec["recipe"], "publication-threshold")
            self.assertEqual(result.detected["table_series"], 4)
            self.assertEqual(result.detected["coordinate_series"], 2)
            self.assertEqual(result.detected["regions"], 2)
            self.assertEqual(result.detected["name_paths"], 2)
            self.assertEqual(spec["metadata"]["migration"]["status"], "draft")

    def test_legacy_method_migration_promotes_implicit_and_annotations(self) -> None:
        source_text = r"""
\begin{axis}[xmin=-2,xmax=2,ymin=-2,ymax=2]
\iipolt[a]{splot y-x} [node[pos=0.25,above] {$L$}];
\iiplot[b]{splot x+y-1} \addpoint{0.3}{45} \addsymbol{0.6}{$B$};
\draw[name intersections={of=a and b,by={c}}] node at(c) {$\calxy{c}$};
\end{axis}
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "legacy-methods.tex"
            source.write_text(source_text, encoding="utf-8")
            result = migrate_legacy_tex(source, root / "migrated")
            spec = load_json(result.spec_path)
            validation = validate_spec(spec, result.spec_path)
            self.assertTrue(validation.ok, validation.errors)
            self.assertEqual(spec["recipe"], "implicit-function")
            self.assertEqual(spec["engine"]["compute"], "gnuplot")
            self.assertEqual(result.detected["implicit_series"], 2)
            self.assertEqual(result.detected["method_annotations"], 3)
            self.assertEqual(result.detected["intersections"], 1)
            self.assertEqual(result.detected["coordinate_refs"], 1)
            annotation_types = [item["type"] for item in spec["annotations"]]
            self.assertIn("curve_probe", annotation_types)
            self.assertIn("curve_label", annotation_types)
            self.assertIn("intersection", annotation_types)
            self.assertIn("coordinate_ref", annotation_types)
            probe = next(item for item in spec["annotations"] if item["type"] == "curve_probe")
            self.assertEqual(probe["position"], 0.3)
            self.assertEqual(probe["pin_angle"], 45.0)

    def test_real_legacy_iiplot_intersection_is_promoted(self) -> None:
        source = PROJECT_ROOT / "references/legacy/tikz-memo/01.tex"
        with tempfile.TemporaryDirectory() as temp:
            result = migrate_legacy_tex(source, temp)
            spec = load_json(result.spec_path)
            self.assertEqual(result.detected["gnuplot_series"], 2)
            self.assertEqual(result.detected["intersections"], 1)
            self.assertEqual(result.detected["coordinate_refs"], 1)
            self.assertEqual(spec["engine"]["compute"], "gnuplot")
            self.assertEqual(
                [item.get("name_path") for item in spec["series"]],
                ["a", "b"],
            )

    def test_non_ascii_legacy_filename_gets_safe_figure_id(self) -> None:
        source = PROJECT_ROOT / "references/legacy/pgfplots-memo/隐函数.tex"
        with tempfile.TemporaryDirectory() as temp:
            result = migrate_legacy_tex(source, temp)
            spec = load_json(result.spec_path)
            self.assertEqual(spec["id"], "legacy-figure-migrated")
            self.assertGreaterEqual(result.detected["implicit_series"], 1)

    def test_unknown_data_binding_is_rejected(self) -> None:
        spec = {
            "schema_version": "1.0",
            "id": "bad-binding",
            "recipe": "function-plot",
            "kind": "pgfplots",
            "axes": {},
            "data_sources": [],
            "series": [{"id": "s", "source": "missing"}],
        }
        result = validate_spec(spec)
        self.assertFalse(result.ok)
        self.assertTrue(any("unknown source" in error for error in result.errors))

    def test_invalid_between_and_error_bindings_are_rejected(self) -> None:
        spec = {
            "schema_version": "1.0",
            "id": "bad-scientific-bindings",
            "recipe": "confidence-band",
            "kind": "pgfplots",
            "axes": {},
            "data_sources": [{"id": "a", "type": "function", "expression": "x"}],
            "series": [
                {
                    "id": "a",
                    "source": "a",
                    "name_path": "A",
                    "error_bars": {"y": {"dir": "both", "mode": "fixed"}},
                }
            ],
            "regions": [{"id": "band", "type": "between", "path_a": "A", "path_b": "missing"}],
        }
        result = validate_spec(spec)
        self.assertFalse(result.ok)
        self.assertTrue(any("requires value" in error for error in result.errors))
        self.assertTrue(any("unknown name_path" in error for error in result.errors))

    def test_render_is_deterministic_and_manifested(self) -> None:
        source_path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        source = load_json(source_path)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            tex_path, first_manifest = render_spec(source, spec_path)
            first = tex_path.read_text(encoding="utf-8")
            tex_path, second_manifest = render_spec(source, spec_path)
            second = tex_path.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(first_manifest["hashes"]["tex_sha256"], second_manifest["hashes"]["tex_sha256"])
            self.assertTrue((root / ".funfig/manifest.json").exists())

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex")
        and shutil.which("pdfinfo") and shutil.which("pdftoppm"),
        "TeX/Poppler QA toolchain unavailable",
    )
    def test_structured_review_history_survives_rebuild(self) -> None:
        source = load_json(PROJECT_ROOT / "examples/golden/flowchart-decision/figure.funfig.json")
        with tempfile.TemporaryDirectory() as temp:
            spec_path = Path(temp) / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            build_spec(source, spec_path)
            inspect_spec(source, spec_path, dpi=100)
            first = mark_visual_review(spec_path, False, "branch label needs more clearance")
            self.assertEqual(first["repair_cycles"], 1)

            build_spec(source, spec_path)
            pending = load_json(spec_path.parent / ".funfig/manifest.json")["qa"]
            self.assertEqual(pending["status"], "not_checked")
            self.assertEqual(pending["repair_cycles"], 1)
            inspect_spec(source, spec_path, dpi=100)
            second = mark_visual_review(spec_path, True, "branch label is clear")
            self.assertEqual(second["review_count"], 2)
            self.assertEqual(second["repair_cycles"], 1)
            self.assertEqual([item["result"] for item in second["review_history"]], ["failed", "passed"])

    @unittest.skipUnless(shutil.which("latexmk") and shutil.which("pdflatex"), "TeX toolchain unavailable")
    def test_build_keeps_stable_artifacts_and_cleans_intermediates(self) -> None:
        source_path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        source = load_json(source_path)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            pdf_path = build_spec(source, spec_path)
            self.assertTrue(pdf_path.exists())
            self.assertTrue((root / "figure.tex").exists())
            self.assertTrue((root / ".funfig/manifest.json").exists())
            self.assertFalse((root / ".funfig/build").exists())
            removed = clean_spec(source, spec_path)
            self.assertEqual(removed, [])
            self.assertTrue(pdf_path.exists())

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex"),
        "TeX toolchain unavailable",
    )
    def test_publication_threshold_builds(self) -> None:
        source_path = PROJECT_ROOT / "examples/publication-threshold/figure.funfig.json"
        source = load_json(source_path)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            pdf_path = build_spec(source, spec_path)
            self.assertTrue(pdf_path.exists())
            tex = (root / "figure.tex").read_text(encoding="utf-8")
            self.assertIn("name intersections={of=A and B,by=I}", tex)
            self.assertIn("funfigIntersectionCallout", tex)

    def test_curated_templates_are_complete_and_searchable(self) -> None:
        items = list_templates()
        self.assertEqual(len(items), 20)
        self.assertEqual(
            {item["id"] for item in items},
            {
                "confidence-band",
                "error-bars",
                "scatter-meta",
                "grouped-panels",
                "surface-colorbar",
                "heatmap-colorbar",
                "decision-branch",
                "feedback-loop",
                "merge-split",
                "layered-framework",
                "grouped-framework",
                "labelled-relations",
                "mediation-model",
                "chain-mediation",
                "direct-effects-model",
                "moderation-model",
                "multi-antecedent-mechanism",
                "business-capability-performance",
                "theory-mechanism-outcomes",
                "experimental-pipeline",
            },
        )
        self.assertEqual(
            get_template("layered-framework")["recipe_hint"],
            "framework-diagram",
        )
        self.assertEqual(
            search_templates("research framework", limit=2)[0]["id"],
            "layered-framework",
        )
        self.assertEqual(
            search_templates("error uncertainty", limit=2)[0]["id"],
            "error-bars",
        )
        self.assertEqual(
            search_templates("feedback return route", limit=2)[0]["id"],
            "feedback-loop",
        )
        self.assertEqual(
            search_templates("merge split parallel inputs", limit=2)[0]["id"],
            "merge-split",
        )
        self.assertEqual(
            search_templates("parallel groups converging outcome", limit=2)[0]["id"],
            "grouped-framework",
        )
        self.assertEqual(search_templates("中介模型", limit=2)[0]["id"], "mediation-model")
        self.assertEqual(search_templates("链式中介", limit=2)[0]["id"], "chain-mediation")
        self.assertEqual(
            search_templates("商学 组织能力 企业绩效", limit=2)[0]["id"],
            "business-capability-performance",
        )
        self.assertEqual(
            search_templates("多自变量 直接效应", limit=2)[0]["id"],
            "direct-effects-model",
        )
        self.assertEqual(search_templates("调节效应", limit=2)[0]["id"], "moderation-model")
        self.assertEqual(
            search_templates("多前因 机制 结果变量", limit=2)[0]["id"],
            "multi-antecedent-mechanism",
        )
        self.assertEqual(
            search_templates("theory mechanism outcome", limit=2)[0]["id"],
            "theory-mechanism-outcomes",
        )
        for item in items:
            with self.subTest(template=item["id"]):
                directory = PROJECT_ROOT / "examples/templates" / item["path"]
                meta = load_json(directory / "template.meta.json")
                self.assertTrue(meta["edit_contract"]["editable"])
                self.assertTrue(meta["edit_contract"]["locked"])
                if meta["family"] in {"flowchart", "framework", "relation", "schematic"}:
                    self.assertTrue(meta["design_fit"]["best_for"])
                    self.assertTrue(meta["design_fit"]["failure_modes"])
                    self.assertEqual(len(meta["design_fit"]["recommended_width_mm"]), 2)
                spec = load_json(directory / "template.funfig.json")
                result = validate_spec(spec)
                self.assertTrue(result.ok, result.errors)

    def test_grid_auto_fit_wraps_nodes_and_expands_center_spacing(self) -> None:
        path = PROJECT_ROOT / "examples/templates/frameworks/business-capability-performance/template.funfig.json"
        spec = load_json(path)
        result = validate_spec(spec, path)
        self.assertTrue(result.ok, result.errors)
        with tempfile.TemporaryDirectory() as temp:
            spec_path = Path(temp) / "figure.funfig.json"
            write_json_atomic(spec_path, spec)
            tex_path, _ = render_spec(spec, spec_path)
            tex = tex_path.read_text(encoding="utf-8")
            self.assertIn("x=53.0mm", tex)
            self.assertIn("y=19.9mm", tex)
            self.assertIn("text width=39.1mm", tex)
            self.assertIn(r"execute at begin node={\hyphenpenalty=10000\relax}", tex)
            self.assertIn("{Organizational capability}", tex)

    def test_relation_edge_can_target_another_edge_midpoint(self) -> None:
        path = PROJECT_ROOT / "examples/templates/relations/moderation-model/template.funfig.json"
        spec = load_json(path)
        result = validate_spec(spec, path)
        self.assertTrue(result.ok, result.errors)
        with tempfile.TemporaryDirectory() as temp:
            spec_path = Path(temp) / "figure.funfig.json"
            write_json_atomic(spec_path, spec)
            tex_path, _ = render_spec(spec, spec_path)
            tex = tex_path.read_text(encoding="utf-8")
            self.assertIn("coordinate[pos=0.5] (funfig_edge_main-effect_mid)", tex)
            self.assertIn("(w) --", tex)
            self.assertIn("(funfig_edge_main-effect_mid);", tex)

        broken = json.loads(json.dumps(spec))
        broken["diagram"]["edges"][1]["to_edge"] = "missing-edge"
        result = validate_spec(broken)
        self.assertFalse(result.ok)
        self.assertTrue(any("unknown edge" in error for error in result.errors))

        cyclic = json.loads(json.dumps(spec))
        cyclic["diagram"]["edges"][0].pop("to")
        cyclic["diagram"]["edges"][0]["to_edge"] = "moderation"
        result = validate_spec(cyclic)
        self.assertFalse(result.ok)
        self.assertTrue(any("target dependencies" in error for error in result.errors))

        invalid_slope = json.loads(json.dumps(spec))
        invalid_slope["diagram"]["edges"][0]["label_sloped"] = "yes"
        result = validate_spec(invalid_slope)
        self.assertFalse(result.ok)
        self.assertTrue(any("label_sloped must be a boolean" in error for error in result.errors))

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex"),
        "TeX toolchain unavailable",
    )
    def test_curated_templates_build_and_match_snapshots(self) -> None:
        for item in list_templates():
            with self.subTest(template=item["id"]), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / "examples/templates" / item["path"]
                work_dir = Path(temp) / item["id"]
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "template.funfig.json"
                spec = load_json(spec_path)
                pdf_path = build_spec(spec, spec_path)
                self.assertTrue(pdf_path.exists())
                generated_tex = work_dir / f"{spec['outputs']['basename']}.tex"
                self.assertEqual(
                    generated_tex.read_text(encoding="utf-8"),
                    (source_dir / "template.tex").read_text(encoding="utf-8"),
                )

    @unittest.skipUnless(
        shutil.which("latexmk")
        and shutil.which("pdflatex")
        and shutil.which("pdfinfo")
        and shutil.which("pdftoppm")
        and shutil.which("pdftotext"),
        "TeX/Poppler QA toolchain unavailable",
    )
    def test_inspect_records_final_size_projection_and_text_metrics(self) -> None:
        item = get_template("layered-framework")
        source_dir = PROJECT_ROOT / "examples/templates" / item["path"]
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp) / "layered-framework"
            shutil.copytree(
                source_dir,
                work_dir,
                ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
            )
            spec_path = work_dir / "template.funfig.json"
            spec = load_json(spec_path)
            build_spec(spec, spec_path)
            qa = inspect_spec(spec, spec_path, dpi=144)
            self.assertTrue(qa["machine_checks_passed"], qa["warnings"])
            self.assertGreater(qa["text_metrics"]["word_count"], 0)
            bbox = qa["text_metrics"]["bbox_height_pt"]
            self.assertGreater(bbox["median"], 0)
            projection = qa["publication_projection"]
            self.assertGreater(projection["width_mm"], 0)
            self.assertGreater(projection["height_mm"], 0)
            self.assertGreater(projection["scale"], 0)
            self.assertLessEqual(projection["scale"], 1.0)
            self.assertEqual(qa["size_check"]["target_source"], "profile:journal-double-column")
            self.assertEqual(qa["size_check"]["target_width_mm"], 178.0)
            manifest = load_json(work_dir / ".funfig/manifest.json")
            self.assertEqual(manifest["qa"]["text_metrics"], qa["text_metrics"])
            self.assertEqual(
                manifest["qa"]["publication_projection"],
                qa["publication_projection"],
            )

    @unittest.skipUnless(
        shutil.which("latexmk")
        and shutil.which("pdflatex")
        and shutil.which("pdfinfo")
        and shutil.which("pdftoppm")
        and shutil.which("pdftotext"),
        "TeX/Poppler QA toolchain unavailable",
    )
    def test_plot_inspect_uses_canvas_width_for_publication_size_check(self) -> None:
        source_dir = PROJECT_ROOT / "examples/basic-function"
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp) / "basic-function"
            shutil.copytree(source_dir, work_dir, ignore=shutil.ignore_patterns("*.pdf", ".funfig", "*.tex"))
            spec_path = work_dir / "figure.funfig.json"
            spec = load_json(spec_path)
            build_spec(spec, spec_path)
            qa = inspect_spec(spec, spec_path, dpi=120)
            self.assertEqual(qa["size_check"]["target_source"], "canvas.width")
            self.assertAlmostEqual(qa["size_check"]["target_width_mm"], 100.0, places=1)
            self.assertEqual(qa["size_check"]["minimum_text_pt"], 7.5)
            self.assertIsNotNone(qa["publication_projection"])
            self.assertGreater(qa["size_check"]["natural_width_mm"], 0)

    @unittest.skipUnless(
        shutil.which("latexmk")
        and shutil.which("pdflatex")
        and shutil.which("pdfinfo")
        and shutil.which("pdftoppm")
        and shutil.which("pdftotext"),
        "TeX/Poppler QA toolchain unavailable",
    )
    def test_inspect_flags_overlapping_text_boxes(self) -> None:
        source_dir = PROJECT_ROOT / "examples/golden/flowchart-decision"
        with tempfile.TemporaryDirectory() as temp:
            work_dir = Path(temp) / "flowchart-overlap"
            shutil.copytree(
                source_dir,
                work_dir,
                ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
            )
            spec_path = work_dir / "figure.funfig.json"
            spec = load_json(spec_path)
            spec["outputs"]["basename"] = "flowchart-overlap"
            spec["diagram"]["layout"]["column_gap"] = "8mm"
            build_spec(spec, spec_path)
            qa = inspect_spec(spec, spec_path, dpi=144)
            self.assertFalse(qa["machine_checks_passed"])
            self.assertGreater(qa["text_metrics"]["bbox_overlap_count"], 0)
            self.assertTrue(
                any("overlapping text bounding-box" in warning for warning in qa["warnings"]),
                qa["warnings"],
            )

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex"),
        "TeX toolchain unavailable",
    )
    def test_publication_goldens_build_from_self_contained_data(self) -> None:
        for case in GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                pdf_path = build_spec(spec, spec_path)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 10_000)
                self.assertFalse((work_dir / ".funfig/build").exists())

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex"),
        "TeX toolchain unavailable",
    )
    def test_scientific_goldens_build_from_self_contained_data(self) -> None:
        for case in SCIENTIFIC_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                pdf_path = build_spec(spec, spec_path)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 5_000)
                self.assertFalse((work_dir / ".funfig/build").exists())

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex") and shutil.which("xelatex"),
        "diagram TeX toolchain unavailable",
    )
    def test_structured_diagram_goldens_build(self) -> None:
        for case in DIAGRAM_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                pdf_path = build_spec(spec, spec_path)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 4_000)
                manifest = load_json(work_dir / ".funfig/manifest.json")
                self.assertEqual(manifest["mode"], "structured")
                self.assertEqual(manifest["qa"]["status"], "not_checked")

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex") and shutil.which("gnuplot"),
        "advanced TeX/gnuplot toolchain unavailable",
    )
    def test_advanced_goldens_build(self) -> None:
        for case in ADVANCED_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                pdf_path = build_spec(spec, spec_path)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 5_000)
                self.assertFalse((work_dir / ".funfig/build").exists())
                self.assertFalse(list(work_dir.glob("*_contourtmp*")))

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex") and shutil.which("gnuplot"),
        "implicit-function toolchain unavailable",
    )
    def test_method_goldens_build(self) -> None:
        for case in METHOD_GOLDEN_CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                source_dir = PROJECT_ROOT / f"examples/golden/{case}"
                work_dir = Path(temp) / case
                shutil.copytree(
                    source_dir,
                    work_dir,
                    ignore=shutil.ignore_patterns("*.pdf", ".funfig"),
                )
                spec_path = work_dir / "figure.funfig.json"
                spec = load_json(spec_path)
                pdf_path = build_spec(spec, spec_path)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 5_000)
                self.assertFalse((work_dir / ".funfig/build").exists())
                self.assertFalse(list(work_dir.glob("*.pgf-plot.gnuplot")))

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex") and shutil.which("gnuplot"),
        "gnuplot toolchain unavailable",
    )
    def test_raw_gnuplot_build_uses_external_compute_and_cleans_intermediates(self) -> None:
        spec = {
            "schema_version": "1.0",
            "id": "raw-gnuplot-smoke",
            "recipe": "function-plot",
            "kind": "pgfplots",
            "engine": {"latex": "pdflatex", "compute": "gnuplot"},
            "axes": {
                "x": {"label": "$x$", "min": -1, "max": 1},
                "y": {"label": "$y$", "min": 0, "max": 1},
                "grid": "major",
            },
            "data_sources": [
                {
                    "id": "gp",
                    "type": "raw_gnuplot",
                    "script": "set samples 40;\nplot x*x;",
                }
            ],
            "series": [{"id": "gp", "source": "gp", "label": "$x^2$"}],
            "outputs": {"basename": "figure", "keep_build": False},
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, spec)
            pdf_path = build_spec(spec, spec_path)
            self.assertTrue(pdf_path.exists())
            self.assertFalse((root / ".funfig/build").exists())
            self.assertFalse((root / "figure.pgf-plot.gnuplot").exists())
            self.assertFalse((root / "figure.pgf-plot.table").exists())


if __name__ == "__main__":
    unittest.main()
