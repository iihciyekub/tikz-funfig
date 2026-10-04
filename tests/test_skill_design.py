from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from funfig.paths import PROJECT_ROOT
from funfig.templates import search_templates


class SkillDesignContractTests(unittest.TestCase):
    def test_design_fixtures_are_retrievable_inputs_not_agent_evals(self) -> None:
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
        repair = by_id["existing-figure-repair"]
        self.assertEqual(repair["task"], "repair")
        expert = by_id["expert-angle-annotation"]
        self.assertEqual(expert["render_mode"], "expert")

    def test_skill_references_resolve_without_locking_prompt_wording(self) -> None:
        refs = PROJECT_ROOT / "packages/skill/references"
        skills = [PROJECT_ROOT / "packages/skill/SKILL.md", *sorted(
            (PROJECT_ROOT / "packages/skills").glob("*/SKILL.md"))]
        for path in [*skills, *refs.glob("*.md")]:
            text = path.read_text(encoding="utf-8")
            for name in set(re.findall(r"`([a-z][a-z-]+\.md)`", text)):
                with self.subTest(file=path.name, reference=name):
                    self.assertTrue((refs / name).is_file())
            for name in re.findall(r"\]\((references/[^)]+\.md)\)", text):
                self.assertTrue((path.parent / name).is_file())

    def test_all_six_skill_metadata_remain_discoverable_and_compact(self) -> None:
        paths = [PROJECT_ROOT / "packages/skill/SKILL.md", *sorted(
            (PROJECT_ROOT / "packages/skills").glob("*/SKILL.md"))]
        names = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            name = re.search(r"^name: (.+)$", text, re.MULTILINE).group(1)
            description = re.search(r"^description: (.+)$", text, re.MULTILINE).group(1)
            names.append(name)
            self.assertRegex(name, r"^[a-z][a-z0-9-]+$")
            # Project discovery budget, not an OpenAI format limit.
            self.assertLessEqual(len(description), 180, path.name)
            self.assertIn("allow_implicit_invocation: true", (path.parent / "agents/openai.yaml").read_text())
        self.assertEqual(len(set(names)), 6)

    def test_public_capability_surface_stays_inside_core_academic_scope(self) -> None:
        menu = (PROJECT_ROOT / "packages/skill/references/capability-menu.md").read_text(encoding="utf-8")
        self.assertIn("社会科学与商学框架", menu)
        self.assertIn("数学模型与关系图", menu)
        self.assertIn("数据与函数图", menu)
        self.assertIn("流程图", menu)
        self.assertIn("长尾/", menu)
        self.assertNotIn("| 规则化复杂几何 |", menu)

        manifest = json.loads((PROJECT_ROOT / "packages/skills/index.json").read_text())
        relations = next(s for s in manifest["skills"] if s["skill_id"] == "funfig-relations")
        self.assertIn("petri-net", relations["recipe_ids"])
        for skill in manifest["skills"]:
            capabilities = set()
            for recipe_id in skill["recipe_ids"]:
                recipe = json.loads((PROJECT_ROOT / "recipes" / f"{recipe_id}.recipe.json").read_text())
                capabilities.update(recipe["capabilities"])
            self.assertTrue(set(skill["capability_ids"]) <= capabilities)

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
