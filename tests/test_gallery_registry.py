from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "tff_gallery.py"
SPEC = importlib.util.spec_from_file_location("tff_gallery", MODULE_PATH)
assert SPEC and SPEC.loader
gallery = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gallery
SPEC.loader.exec_module(gallery)


class GalleryRegistryTests(unittest.TestCase):
    def test_registry_matches_examples(self) -> None:
        committed = gallery.normalized_registry(json.loads((ROOT / "gallery" / "registry.json").read_text(encoding="utf-8")))
        expected = gallery.normalized_registry(gallery.compute_registry(ROOT / "gallery" / "registry.json"))
        self.assertEqual(committed, expected)

    def test_ids_are_unique_and_never_overlap_retired(self) -> None:
        data = json.loads((ROOT / "gallery" / "registry.json").read_text(encoding="utf-8"))
        active = [item["id"] for item in data["entries"]]
        retired = [item["id"] for item in data["retired"]]
        self.assertEqual(len(active), len(set(active)))
        self.assertFalse(set(active) & set(retired))
        self.assertTrue(all(gallery.ID_RE.fullmatch(value) for value in active + retired))

    def test_every_active_entry_resolves(self) -> None:
        data = gallery.enriched_registry(ROOT / "gallery" / "registry.json")
        self.assertEqual(len(data["entries"]), 53)
        for item in data["entries"]:
            self.assertTrue((ROOT / item["source"]).is_file(), item["id"])


if __name__ == "__main__":
    unittest.main()
