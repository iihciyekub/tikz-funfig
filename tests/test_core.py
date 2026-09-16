from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from funfig.build import build_spec, clean_spec
from funfig.io import load_json, write_json_atomic
from funfig.paths import PROJECT_ROOT
from funfig.recipes import recipe_ids
from funfig.render import render_spec
from funfig.schema import validate_spec


class FunFigCoreTests(unittest.TestCase):
    def test_recipe_registry(self) -> None:
        self.assertEqual(
            recipe_ids(),
            [
                "function-plot",
                "data-series",
                "threshold-region",
                "intersection-curves",
                "groupplot",
                "mechanism-diagram",
            ],
        )

    def test_basic_example_validates(self) -> None:
        path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        spec = load_json(path)
        result = validate_spec(spec, path)
        self.assertTrue(result.ok, result.errors)

    def test_unknown_data_binding_is_rejected(self) -> None:
        spec = {
            "schema_version": "1.0",
            "id": "bad-binding",
            "recipe": "function-plot",
            "kind": "pgfplots",
            "axes": {},
            "data_sources": [],
            "series": [{"id": "s", "source": "missing"}],
        }
        result = validate_spec(spec)
        self.assertFalse(result.ok)
        self.assertTrue(any("unknown source" in error for error in result.errors))

    def test_render_is_deterministic_and_manifested(self) -> None:
        source_path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        source = load_json(source_path)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            tex_path, first_manifest = render_spec(source, spec_path)
            first = tex_path.read_text(encoding="utf-8")
            tex_path, second_manifest = render_spec(source, spec_path)
            second = tex_path.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(first_manifest["hashes"]["tex_sha256"], second_manifest["hashes"]["tex_sha256"])
            self.assertTrue((root / ".funfig/manifest.json").exists())

    @unittest.skipUnless(shutil.which("latexmk") and shutil.which("pdflatex"), "TeX toolchain unavailable")
    def test_build_keeps_stable_artifacts_and_cleans_intermediates(self) -> None:
        source_path = PROJECT_ROOT / "examples/basic-function/figure.funfig.json"
        source = load_json(source_path)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, source)
            pdf_path = build_spec(source, spec_path)
            self.assertTrue(pdf_path.exists())
            self.assertTrue((root / "figure.tex").exists())
            self.assertTrue((root / ".funfig/manifest.json").exists())
            self.assertFalse((root / ".funfig/build").exists())
            removed = clean_spec(source, spec_path)
            self.assertEqual(removed, [])
            self.assertTrue(pdf_path.exists())

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex") and shutil.which("gnuplot"),
        "gnuplot toolchain unavailable",
    )
    def test_raw_gnuplot_build_uses_external_compute_and_cleans_intermediates(self) -> None:
        spec = {
            "schema_version": "1.0",
            "id": "raw-gnuplot-smoke",
            "recipe": "function-plot",
            "kind": "pgfplots",
            "engine": {"latex": "pdflatex", "compute": "gnuplot"},
            "axes": {
                "x": {"label": "$x$", "min": -1, "max": 1},
                "y": {"label": "$y$", "min": 0, "max": 1},
                "grid": "major",
            },
            "data_sources": [
                {
                    "id": "gp",
                    "type": "raw_gnuplot",
                    "script": "set samples 40;\nplot x*x;",
                }
            ],
            "series": [{"id": "gp", "source": "gp", "label": "$x^2$"}],
            "outputs": {"basename": "figure", "keep_build": False},
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec_path = root / "figure.funfig.json"
            write_json_atomic(spec_path, spec)
            pdf_path = build_spec(spec, spec_path)
            self.assertTrue(pdf_path.exists())
            self.assertFalse((root / ".funfig/build").exists())
            self.assertFalse((root / "figure.pgf-plot.gnuplot").exists())
            self.assertFalse((root / "figure.pgf-plot.table").exists())


if __name__ == "__main__":
    unittest.main()

