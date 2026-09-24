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
            "workflow.md": ("focused structural/technical queries", "validate-design"),
            "reference-images.md": ("Style", "do not transfer"),
            "composition.md": ("LaTeX academic character", "target size"),
            "visual-review.md": ("Repair order", "final-size"),
            "expert-mode.md": ("Sourced Expert TikZ mode", "provenance"),
        }
        for name, fragments in required.items():
            text = (refs / name).read_text(encoding="utf-8")
            for fragment in fragments:
                with self.subTest(file=name, fragment=fragment):
                    self.assertIn(fragment.casefold(), text.casefold())


if __name__ == "__main__":
    unittest.main()
