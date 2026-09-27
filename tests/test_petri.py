from __future__ import annotations

import copy
import shutil
import tempfile
import unittest
from pathlib import Path

from funfig.build import build_spec
from funfig.cli import _starter_spec
from funfig.io import load_json
from funfig.paths import PROJECT_ROOT
from funfig.render import render_spec
from funfig.schema import validate_spec


GOLDEN = PROJECT_ROOT / "examples/golden/petri-resource-loop/figure.funfig.json"


class PetriNetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load_json(GOLDEN)

    def test_starter_and_golden_validate(self) -> None:
        self.assertTrue(validate_spec(_starter_spec("petri-net", "starter")).ok)
        self.assertTrue(validate_spec(self.spec, GOLDEN).ok)

    def test_petri_contract_rejects_semantic_errors(self) -> None:
        changes = (
            (lambda s: s["petri"]["arcs"][0].update({"to": "finished"}), "one place and one transition"),
            (lambda s: s["petri"]["arcs"].append(copy.deepcopy(s["petri"]["arcs"][0])), "duplicates a directed arc"),
            (lambda s: s["petri"]["places"][0].update({"tokens": -1}), "non-negative integer"),
            (lambda s: s["petri"]["places"][0].update({"tokens": True}), "non-negative integer"),
            (lambda s: s["petri"]["arcs"][1].update({"weight": 0}), "positive integer"),
            (lambda s: s["petri"]["transitions"][0].update({"id": "waiting"}), "IDs must be disjoint"),
            (lambda s: s["petri"]["places"][0].update({"position": {"x": 0}}), "finite numeric x and y"),
        )
        for change, expected in changes:
            with self.subTest(expected=expected):
                spec = copy.deepcopy(self.spec)
                change(spec)
                self.assertIn(expected, "\n".join(validate_spec(spec).errors))

    def test_golden_tex_is_deterministic_and_preserves_weights(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            spec_path.write_bytes(GOLDEN.read_bytes())
            tex_path, manifest = render_spec(self.spec, spec_path)
            source = tex_path.read_text(encoding="utf-8")
            self.assertEqual(source, GOLDEN.with_name("petri-resource-loop.tex").read_text(encoding="utf-8"))
            self.assertIn("tokens=2", source)
            self.assertIn("tokens=3", source)
            self.assertIn("tokens=0", source)
            self.assertEqual(source.count("node[midway,above,fill=white,inner sep=1pt] {2}"), 2)
            self.assertEqual(manifest["renderer"], "petri")

    def test_large_marking_uses_number_instead_of_unsupported_token_style(self) -> None:
        spec = copy.deepcopy(self.spec)
        spec["petri"]["places"][0]["tokens"] = 10
        with tempfile.TemporaryDirectory() as temp:
            spec_path = Path(temp) / "figure.funfig.json"
            spec_path.write_text("{}", encoding="utf-8")
            source = render_spec(spec, spec_path)[0].read_text(encoding="utf-8")
            self.assertIn("{\\scriptsize 10}", source)
            self.assertNotIn("tokens=10", source)

    @unittest.skipUnless(shutil.which("latexmk") and shutil.which("pdflatex"), "TeX toolchain unavailable")
    def test_golden_builds_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            spec_path.write_bytes(GOLDEN.read_bytes())
            pdf = build_spec(self.spec, spec_path)
            self.assertGreater(pdf.stat().st_size, 4_000)


if __name__ == "__main__":
    unittest.main()
