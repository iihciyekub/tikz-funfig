from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("skill_behavior", ROOT / "benchmarks/skill-behavior/run_cases.py")
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class SkillBehaviorGraderTests(unittest.TestCase):
    def test_self_report_is_not_invocation_or_visual_evidence(self) -> None:
        events = [{"type": "item.completed", "item": {"type": "agent_message",
                   "text": "I read skills/funfig-plots/SKILL.md and used view_image."}}]
        self.assertEqual(runner.execution_evidence(events), (set(), "", False))
        command_claim = [{"type": "item.completed", "item": {"type": "command_execution",
                         "exit_code": 0, "command": "echo 'I used view_image'"}}]
        self.assertFalse(runner.execution_evidence(command_claim)[2])

    def test_successful_tool_read_counts_but_failed_read_does_not(self) -> None:
        def event(code):
            return {"type": "item.completed", "item": {"type": "command_execution",
                    "command": "cat .agents/skills/funfig-relations/SKILL.md", "exit_code": code}}
        self.assertEqual(runner.execution_evidence([event(0)])[0], {"funfig-relations"})
        self.assertFalse(runner.execution_evidence([event(1)])[0])

    def test_literal_math_labels_preserve_content(self) -> None:
        self.assertEqual(runner.semantic_label("$X$"), "X")
        self.assertEqual(runner.semantic_label("X"), "X")
        self.assertNotEqual(runner.semantic_label("$X_1$"), "X")

    def test_help_only_and_negative_controls_reject_files_or_wrong_reads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            events = [{"type": "turn.completed"}, {"type": "item.completed", "item": {
                "type": "command_execution", "command": "cat .agents/skills/TIKZ-FunFig/SKILL.md", "exit_code": 0}}]
            case = {"id": "help", "prompt": "how to use it", "skills": ["TIKZ-FunFig"], "help_link": True,
                    "no_output": True, "forbidden_reads": ["workflow.md"]}
            link = "https://iihciyekub.github.io/tikz-funfig/"
            self.assertTrue(runner.grade(case, workspace, events, link, 0, {})["passed"])
            (workspace / "unexpected.tex").write_text("unexpected")
            self.assertFalse(runner.grade(case, workspace, events, link, 0, {})["passed"])
            (workspace / "unexpected.tex").unlink()
            self.assertFalse(runner.grade({"id": "negative", "prompt": "explain", "skills": []}, workspace, events, "", 0, {})["passed"])
            self.assertFalse(runner.grade(case, workspace, events, link, 124, {})["passed"])

    def test_native_explicit_injection_requires_actual_supporting_resource_use(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = {"id": "explicit", "prompt": "Use $funfig-flowcharts", "skills": ["funfig-flowcharts"]}
            events = [{"type": "turn.completed"}, {"type": "item.completed", "item": {
                "type": "command_execution", "exit_code": 0,
                "command": "cat .agents/skills/TIKZ-FunFig/references/workflow.md"}}]
            self.assertTrue(runner.grade(case, Path(temp), events, "", 0, {})["passed"])
            self.assertFalse(runner.grade(case, Path(temp), events[:1], "I used the skill", 0, {})["passed"])

    def test_real_case_set_covers_each_family_negatives_and_delivery(self) -> None:
        cases = json.loads((ROOT / "benchmarks/skill-behavior/cases.json").read_text())["cases"]
        self.assertEqual(len({c["id"] for c in cases}), 24)
        self.assertGreaterEqual(sum(not c["skills"] for c in cases), 4)
        self.assertGreaterEqual(sum(c.get("delivery", False) for c in cases), 6)
        self.assertEqual(set.union(*(set(c["skills"]) for c in cases)),
                         {"TIKZ-FunFig", "funfig-plots", "funfig-flowcharts", "funfig-frameworks",
                          "funfig-relations", "funfig-schematics"})


if __name__ == "__main__":
    unittest.main()
