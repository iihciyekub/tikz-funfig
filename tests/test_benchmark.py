from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from funfig.paths import PROJECT_ROOT


module_path = PROJECT_ROOT / "benchmarks/reference-reproduction/collect_results.py"
module_spec = importlib.util.spec_from_file_location("collect_results", module_path)
assert module_spec and module_spec.loader
collector = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(collector)

paper_module_path = PROJECT_ROOT / "benchmarks/paper-visual/run_cases.py"
paper_module_spec = importlib.util.spec_from_file_location("paper_visual_runner", paper_module_path)
assert paper_module_spec and paper_module_spec.loader
paper_runner = importlib.util.module_from_spec(paper_module_spec)
paper_module_spec.loader.exec_module(paper_runner)


class BenchmarkCollectorTests(unittest.TestCase):
    def test_blind_rubric_and_missing_cases_gate_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "cases.json"
            fixture.write_text(json.dumps({"cases": [
                {"id": "present", "expected_route": "structured", "blind_required": True,
                 "reference_url": "https://example.test/reference.png"},
                {"id": "missing", "expected_route": "expert", "blind_required": True},
            ]}), encoding="utf-8")
            case = root / "present"
            (case / ".funfig").mkdir(parents=True)
            (case / "figure.design.json").write_text(json.dumps({
                "id": "present", "render_mode": "structured",
                "appearance": {"target_width_mm": 88},
                "routing": {"decision": "structured"},
            }), encoding="utf-8")
            (case / ".funfig/manifest.json").write_text(json.dumps({"qa": {
                "status": "passed", "visual_review": "passed", "machine_checks_passed": True,
                "size_check": {"natural_width_mm": 80},
            }}), encoding="utf-8")
            review = {
                "schema_version": "1.0", "reviewer": "agent", "source_exposure": "none",
                "reference_locator": "https://example.test/reference.png",
                "scores": {name: {"result": "pass", "evidence": f"Checked {name} against reference."}
                           for name in ("semantics", "geometry", "readability", "reference_alignment")},
            }
            review_path = case / "reference-review.json"
            review_path.write_text(json.dumps(review), encoding="utf-8")

            report = collector.collect(root, fixture)
            self.assertEqual((report["case_count"], report["passed_count"], report["failed_count"]), (2, 1, 1))
            present = next(item for item in report["results"] if item["case_id"] == "present")
            self.assertTrue(present["passed"])
            self.assertTrue(present["width_pass"])

            narrow_design = json.loads((case / "figure.design.json").read_text())
            narrow_design["appearance"]["target_width_mm"] = 70
            (case / "figure.design.json").write_text(json.dumps(narrow_design), encoding="utf-8")
            narrow = next(item for item in collector.collect(root, fixture)["results"]
                          if item["case_id"] == "present")
            self.assertFalse(narrow["width_pass"])
            self.assertFalse(narrow["passed"])
            narrow_design["appearance"]["target_width_mm"] = 88
            (case / "figure.design.json").write_text(json.dumps(narrow_design), encoding="utf-8")

            review["source_exposure"] = "partial"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            self.assertFalse(next(item for item in collector.collect(root, fixture)["results"]
                                  if item["case_id"] == "present")["passed"])

            review["source_exposure"] = "none"
            review["scores"]["geometry"]["evidence"] = ""
            review_path.write_text(json.dumps(review), encoding="utf-8")
            self.assertFalse(next(item for item in collector.collect(root, fixture)["results"]
                                  if item["case_id"] == "present")["passed"])

    def test_paper_visual_cases_prepare_valid_structured_and_plot_specs(self) -> None:
        cases = json.loads((PROJECT_ROOT / "benchmarks/paper-visual/cases.json").read_text())["cases"]
        self.assertEqual(len(cases), 5)
        with tempfile.TemporaryDirectory() as temp:
            for case in cases:
                with self.subTest(case=case["id"]):
                    spec, path = paper_runner.prepare(case, Path(temp) / case["id"])
                    self.assertEqual(spec["id"], case["id"])
                    self.assertTrue(path.is_file())

if __name__ == "__main__":
    unittest.main()
