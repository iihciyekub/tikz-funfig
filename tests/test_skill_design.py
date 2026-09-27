from __future__ import annotations

import json
import unittest
from pathlib import Path

from funfig.paths import PROJECT_ROOT
from funfig.templates import search_templates


class SkillDesignContractTests(unittest.TestCase):
    def test_end_to_end_skill_cases_are_structured_and_retrievable(self) -> None:
        fixture = json.loads(
            (PROJECT_ROOT / "tests/fixtures/skill-design-cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["schema_version"], "1.0")
        self.assertEqual(len(fixture["cases"]), 4)
        by_id = {case["id"]: case for case in fixture["cases"]}
        merge = by_id["text-merge-split"]
        self.assertEqual(
            search_templates(merge["query_rewrites"][0], limit=1)[0]["id"],
            merge["expected_template"],
        )
        style_case = by_id["reference-style-new-content"]
        self.assertEqual(style_case["reference_roles"], ["style"])
        self.assertTrue(any("do not copy reference facts" in item for item in style_case["acceptance"]))
        repair = by_id["existing-figure-repair"]
        self.assertTrue(any("layout before reducing text size" in item for item in repair["acceptance"]))
        expert = by_id["expert-angle-annotation"]
        self.assertEqual(expert["render_mode"], "expert")
        self.assertTrue(any("provenance" in item for item in expert["acceptance"]))

    def test_shared_skill_references_cover_the_four_eval_modes(self) -> None:
        refs = PROJECT_ROOT / "packages/skill/references"
        required = {
            "scope-boundary.md": ("Core capability", "Long-tail / experimental capability", "Out of scope"),
            "workflow.md": ("focused structural/technical queries", "validate-design"),
            "reference-images.md": ("Style", "do not transfer"),
            "routing.md": ("Decision rules", "unsupported_features"),
            "expert-patterns.md": ("Expert pattern planner", "hidden-edge-logic"),
            "structure-inference.md": ("Infer rules before objects", "fit_polar_geometry.py"),
            "generative-geometry.md": ("Generative geometry mode", "complete_edges"),
            "density-aware-styling.md": ("Density-aware styling", "Drawing nodes last"),
            "parameter-search.md": ("Coarse-to-fine workflow", "generative-variants"),
            "symmetry-and-constraints.md": ("Symmetry and structural constraints", "model symmetry"),
            "composition.md": ("LaTeX academic character", "target size"),
            "visual-review.md": ("Defect-led repair loop", "reference alignment"),
            "expert-mode.md": ("Sourced Expert TikZ mode", "provenance"),
        }
        for name, fragments in required.items():
            text = (refs / name).read_text(encoding="utf-8")
            for fragment in fragments:
                with self.subTest(file=name, fragment=fragment):
                    self.assertIn(fragment.casefold(), text.casefold())

    def test_public_capability_surface_stays_inside_core_academic_scope(self) -> None:
        menu = (PROJECT_ROOT / "packages/skill/references/capability-menu.md").read_text(encoding="utf-8")
        self.assertIn("社会科学与商学框架", menu)
        self.assertIn("数学模型与关系图", menu)
        self.assertIn("数据与函数图", menu)
        self.assertIn("流程图", menu)
        self.assertIn("长尾/", menu)
        self.assertNotIn("| 规则化复杂几何 |", menu)

        general = (PROJECT_ROOT / "packages/skill/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scope-boundary.md", general)
        self.assertIn("Social/business research framework", general)
        self.assertIn("Variables, mathematical models", general)

        routing = (PROJECT_ROOT / "packages/skill/references/routing.md").read_text(encoding="utf-8")
        self.assertIn("Do not proactively route", routing)
        self.assertIn("user explicitly requested that long-tail geometry", routing)

        generative = (PROJECT_ROOT / "packages/skill/references/generative-geometry.md").read_text(encoding="utf-8")
        self.assertIn("long-tail / experimental", generative.casefold())
        self.assertIn("not a default TIKZ-FunFig product surface", generative)

        scope = (PROJECT_ROOT / "packages/skill/references/scope-boundary.md").read_text(encoding="utf-8")
        for excluded in ("CAD/EDA", "animation", "GIS/map", "statistical inference"):
            with self.subTest(excluded=excluded):
                self.assertIn(excluded.casefold(), scope.casefold())

    def test_plugin_metadata_promotes_paper_figures_not_long_tail_geometry(self) -> None:
        plugin = json.loads((PROJECT_ROOT / "packages/plugin/tikz-funfig/plugin.json").read_text(encoding="utf-8"))
        interface = plugin["extensions"]["com.openai"]["interface"]
        description = interface["longDescription"].casefold()
        for expected in ("function/data plots", "research frameworks", "flowcharts"):
            self.assertIn(expected.casefold(), description)
        for excluded in ("fractals", "tilings", "3d", "circuit"):
            self.assertNotIn(excluded, description)

    def test_reference_reproduction_benchmark_covers_route_pattern_and_qa_contracts(self) -> None:
        fixture = json.loads(
            (PROJECT_ROOT / "benchmarks/reference-reproduction/cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual(fixture["schema_version"], "1.0")
        self.assertGreaterEqual(len(fixture["cases"]), 5)
        by_id = {case["id"]: case for case in fixture["cases"]}
        self.assertEqual(by_id["rotated-sphere"]["expected_route"], "expert")
        self.assertIn("projected-wireframe", by_id["rotated-sphere"]["expected_patterns"])
        self.assertIn("hidden-edge-logic", by_id["hexagonal-prism"]["expected_patterns"])
        self.assertTrue(any("deterministic" in item for item in by_id["procedural-city"]["acceptance"]))
        self.assertIn("complete_edges", by_id["circular-chord-network"]["expected_generators"])
        self.assertIn("lattice_cells", by_id["triangular-lattice-tiling"]["expected_generators"])
        self.assertIn("koch_snowflake", by_id["koch-snowflake-fractal"]["expected_generators"])
        self.assertIn("projected_box", by_id["projected-box-cluster"]["expected_generators"])


if __name__ == "__main__":
    unittest.main()
