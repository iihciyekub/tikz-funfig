from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from funfig.cli import _starter_spec, main
from funfig.design import validate_design
from funfig.io import load_json, write_json_atomic
from funfig.manifest import sha256_file
from funfig.paths import PROJECT_ROOT


GOLDEN = PROJECT_ROOT / "examples/golden/flowchart-decision/figure.design.json"


class DesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "figure.design.json"
        self.design = load_json(GOLDEN)
        write_json_atomic(self.path, self.design)

    def test_golden_design_agrees_with_existing_figurespec(self) -> None:
        self.assertEqual(validate_design(GOLDEN)["id"], "flowchart-decision")

    def test_invalid_reference_roles_sizes_and_paths_are_rejected(self) -> None:
        invalid = [
            ("path traversal", {"delivery": {"basename": "../figure", "formats": ["pdf"]}}),
            ("PDF required", {"delivery": {"basename": "figure", "formats": ["svg"]}}),
            ("unknown mode", {"render_mode": "automatic"}),
            ("unknown property", {"invented_field": True}),
            ("blank intent", {"intent": "   "}),
            ("expert provenance", {"render_mode": "expert", "knowledge_sources": []}),
            ("unknown reference role", {"references": [{"locator": "attachment:1", "roles": ["inspiration"], "adopt": [], "do_not_transfer": []}]}),
            ("boolean width", {"appearance": {**self.design["appearance"], "target_width_mm": True}}),
            ("zero width", {"appearance": {**self.design["appearance"], "target_width_mm": 0}}),
            ("infinite width", {"appearance": {**self.design["appearance"], "target_width_mm": float("inf")}}),
        ]
        for label, updates in invalid:
            with self.subTest(label=label):
                write_json_atomic(self.path, {**self.design, **updates})
                with self.assertRaises(ValueError):
                    validate_design(self.path)

    def test_reference_can_be_style_only_and_expert_has_common_contract(self) -> None:
        self.design["references"] = [{
            "locator": "attachment: style reference",
            "roles": ["style"],
            "adopt": ["Thin monochrome lines"],
            "do_not_transfer": ["Scientific values and labels"],
        }]
        self.design["render_mode"] = "expert"
        self.design["knowledge_sources"] = ["pgfmanual-3.1.11a-p0128-0129"]
        write_json_atomic(self.path, self.design)
        self.assertEqual(validate_design(self.path)["references"][0]["roles"], ["style"])

    def test_source_identity_and_format_drift_are_rejected(self) -> None:
        spec = _starter_spec("flowchart", self.design["id"])
        spec["outputs"]["basename"] = self.design["delivery"]["basename"]
        for field, value in [("id", "different-id"), ("basename", "other"), ("formats", ["pdf", "svg"])]:
            with self.subTest(field=field):
                changed = copy.deepcopy(spec)
                if field == "id":
                    changed[field] = value
                else:
                    changed["outputs"][field] = value
                write_json_atomic(self.root / "figure.funfig.json", changed)
                with self.assertRaisesRegex(ValueError, "differs|differ"):
                    validate_design(self.path)

    def _synthetic_delivery(self, mode: str) -> Path:
        # A filesystem/state validation fixture, not a compiled or visually
        # reviewed real figure. Actual rendering is covered by build regressions.
        self.design["render_mode"] = mode
        write_json_atomic(self.path, self.design)
        basename = self.design["delivery"]["basename"]
        artifacts = {"tex": f"{basename}.tex", "pdf": f"{basename}.pdf"}
        for name in artifacts.values():
            (self.root / name).write_text("synthetic delivery validation fixture")
        if mode == "structured":
            spec = _starter_spec("flowchart", self.design["id"])
            spec["outputs"]["basename"] = basename
            write_json_atomic(self.root / "figure.funfig.json", spec)
            artifacts["spec"] = "figure.funfig.json"
        manifest = self.root / ".funfig" / ("manifest.json" if mode == "structured" else "expert-manifest.json")
        write_json_atomic(manifest, {
            "status": "built", "mode": "structured" if mode == "structured" else "raw-expert",
            "hashes": {f"{kind}_sha256": sha256_file(self.root / name) for kind, name in artifacts.items()},
            "qa": {"status": "passed", "visual_review": "passed", "machine_checks_passed": True, "review_note": "synthetic test fixture"},
        })
        return manifest

    def test_delivery_checks_pending_review_missing_files_and_unresolved_content(self) -> None:
        manifest = self._synthetic_delivery("structured")
        validate_design(self.path, delivery=True)
        record = load_json(manifest)
        record["qa"]["visual_review"] = "pending"
        write_json_atomic(manifest, record)
        with self.assertRaisesRegex(ValueError, "actual recorded visual review"):
            validate_design(self.path, delivery=True)
        record["qa"]["visual_review"] = "passed"
        write_json_atomic(manifest, record)
        self.design["content"]["unresolved"] = ["Unreadable branch label"]
        write_json_atomic(self.path, self.design)
        with self.assertRaisesRegex(ValueError, "unresolved content"):
            validate_design(self.path, delivery=True)
        (self.root / f"{self.design['delivery']['basename']}.pdf").unlink()
        with self.assertRaisesRegex(ValueError, "missing delivery artifact"):
            validate_design(self.path, delivery=True)

    def test_delivery_rejects_changed_source_and_pdf_in_both_modes(self) -> None:
        for mode in ("structured", "expert"):
            for suffix in ("tex", "pdf"):
                with self.subTest(mode=mode, suffix=suffix):
                    self._synthetic_delivery(mode)
                    validate_design(self.path, delivery=True)
                    artifact = self.root / f"{self.design['delivery']['basename']}.{suffix}"
                    artifact.write_text("changed after build/review")
                    with self.assertRaisesRegex(ValueError, "stale or missing build hash"):
                        validate_design(self.path, delivery=True)

    def test_cli_reports_missing_design_without_traceback(self) -> None:
        self.assertEqual(main(["validate-design", str(self.root / "absent.json")]), 2)

    def test_design_schema_and_references_work_in_isolated_plugin(self) -> None:
        plugin = self.root / "plugin"
        source = PROJECT_ROOT / "packages/plugin/tikz-funfig"
        shutil.copytree(source, plugin, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.assertEqual(
            (PROJECT_ROOT / "schemas/figure-design.schema.json").read_bytes(),
            (plugin / "runtime/schemas/figure-design.schema.json").read_bytes(),
        )
        for name in ("workflow.md", "reference-images.md", "composition.md", "design-contract.md", "visual-review.md", "expert-mode.md"):
            self.assertEqual(
                (PROJECT_ROOT / "packages/skill/references" / name).read_bytes(),
                (plugin / "skills/TIKZ-FunFig/references" / name).read_bytes(),
            )
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [str(plugin / "skills/funfig-flowcharts/scripts/funfig.sh"), "validate-design", str(self.path)],
            cwd=self.root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
