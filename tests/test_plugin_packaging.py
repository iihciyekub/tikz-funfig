from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PluginPackagingTests(unittest.TestCase):
    def test_sync_preserves_source_builds_without_bundling_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            for name in ("packages/skill", "packages/skills", "src/funfig", "schemas",
                         "recipes", "themes", "profiles", "knowledge", "examples", "gallery"):
                shutil.copytree(ROOT / name, repo / name,
                                ignore=shutil.ignore_patterns(".funfig", "*.pdf", "__pycache__", "*.pyc"))
            for name in ("pyproject.toml", "scripts/tff", "scripts/sync_plugin_package.sh",
                         "scripts/check_plugin_bundle.py", "packages/plugin/tikz-funfig/plugin.json",
                         "IconKitchen/macos/AppIcon128.png", "IconKitchen/macos/AppIcon512.png"):
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            case = repo / "examples/golden/flowchart-feedback"
            (case / ".funfig").mkdir()
            leftovers = [case / "local.pdf", case / "local.aux", case / "local.log",
                         case / ".funfig/manifest.json", case / ".funfig/preview.png"]
            for path in leftovers:
                path.write_bytes(b"local build evidence")
            subprocess.run([str(repo / "scripts/sync_plugin_package.sh")], check=True, capture_output=True)
            subprocess.run(["python3", str(repo / "scripts/check_plugin_bundle.py")],
                           check=True, capture_output=True)
            bundled = repo / "packages/plugin/tikz-funfig/runtime/gallery/examples/golden/flowchart-feedback"
            self.assertTrue((bundled / "figure.funfig.json").is_file())
            for path in leftovers:
                self.assertEqual(path.read_bytes(), b"local build evidence")
                self.assertFalse((bundled / path.relative_to(case)).exists())


if __name__ == "__main__":
    unittest.main()
