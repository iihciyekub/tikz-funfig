from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is needed to execute the actual browser prompt module")
class GalleryPromptTests(unittest.TestCase):
    def prompt(self, item: dict, language: str = "zh") -> str:
        code = "const p=require(process.argv[1]); process.stdout.write(p.promptFor(JSON.parse(process.argv[2]),process.argv[3]));"
        return subprocess.check_output(["node", "-e", code, str(ROOT / "gallery/site/prompts.js"),
                                        json.dumps(item), language], text=True)

    def test_card_prompts_preserve_exact_id_and_request_user_content(self) -> None:
        families = ("flowchart", "framework", "relation", "plot", "schematic", "petri-net", "graph")
        for family in families:
            with self.subTest(family=family):
                prompt = self.prompt({"id": "TFF-0042", "family": family})
                self.assertIn("TFF-0042", prompt)
                self.assertIn("[", prompt)
                self.assertIn("我的事实、标签、数据和关系", prompt)
                self.assertIn("可编辑源码和 PDF", prompt)
                self.assertNotIn("Resolve the exact registry", prompt)

    def test_family_examples_distinguish_process_groups_paths_and_measurements(self) -> None:
        self.assertIn("步骤、判断条件", self.prompt({"id": "TFF-0033", "family": "flowchart"}))
        self.assertIn("层级、分组", self.prompt({"id": "TFF-0037", "family": "framework"}))
        self.assertIn("调节哪条路径", self.prompt({"id": "TFF-0048", "family": "relation"}))
        self.assertIn("误差范围请说明定义", self.prompt({"id": "TFF-0042", "family": "error-bar"}))

    def test_english_prompts_preserve_the_same_content_and_delivery_contract(self) -> None:
        for family in ("flowchart", "framework", "relation", "plot", "schematic", "petri-net", "graph"):
            with self.subTest(family=family):
                prompt = self.prompt({"id": "TFF-0051", "family": family}, "en")
                self.assertIn("TFF-0051", prompt)
                self.assertIn("my facts, labels, data, and relationships", prompt)
                self.assertIn("editable source and PDF", prompt)
                self.assertNotRegex(prompt, r"[\u4e00-\u9fff]")
        self.assertIn("path each moderator affects", self.prompt({"id": "TFF-0051", "family": "relation"}, "en"))
        self.assertIn("define uncertainty", self.prompt({"id": "TFF-0042", "family": "plot"}, "en"))

    def test_every_visible_example_has_chinese_title_and_description(self) -> None:
        code = "const l=require(process.argv[1]); process.stdout.write(JSON.stringify(l.entriesZh));"
        translated = json.loads(subprocess.check_output(["node", "-e", code,
                                str(ROOT / "gallery/site/i18n.js")], text=True))
        registry = json.loads((ROOT / "gallery/registry.json").read_text())
        visible = {e["id"] for e in registry["entries"] if e.get("gallery_visibility") != "hidden"}
        self.assertEqual(set(translated), visible)
        for title, description in translated.values():
            self.assertRegex(title, r"[\u4e00-\u9fff]")
            self.assertRegex(description, r"[\u4e00-\u9fff]")

    def test_built_site_contains_prompt_module_and_help_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "site"
            subprocess.run(["python3", str(ROOT / "scripts/tff_gallery.py"), "build-site",
                            "--skip-previews", "--output", str(output)], check=True, capture_output=True)
            html = (output / "index.html").read_text()
            self.assertLess(html.index('src="i18n.js"'), html.index('src="app.js"'))
            self.assertLess(html.index('src="prompts.js"'), html.index('src="app.js"'))
            self.assertTrue((output / "prompts.js").is_file())
            self.assertTrue((output / "i18n.js").is_file())
            self.assertIn("https://iihciyekub.github.io/tikz-funfig/", (output / "llms.txt").read_text())
            self.assertEqual(len(json.loads((output / "registry.json").read_text())["entries"]), 59)


if __name__ == "__main__":
    unittest.main()
