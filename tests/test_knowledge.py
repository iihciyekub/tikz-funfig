from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from funfig.knowledge import knowledge_root, search, status
from funfig.paths import PROJECT_ROOT


class KnowledgeTests(unittest.TestCase):
    def test_knowledge_status_has_compiled_cards_and_manual_corpus(self) -> None:
        payload = status()
        self.assertEqual(Path(payload["root"]), knowledge_root())
        self.assertEqual(payload["cards"], 24)
        self.assertGreaterEqual(payload["manual_chunks"], 800)
        self.assertEqual(payload["verification"]["compiled"], 24)
        self.assertEqual(payload["verification"]["draft"], 0)

    def test_alias_search_prefers_verified_card_then_official_source(self) -> None:
        hits = search("相对定位", limit=6)
        self.assertGreaterEqual(len(hits), 2)
        self.assertEqual(hits[0].id, "relative-positioning")
        self.assertEqual(hits[0].kind, "card")
        self.assertEqual(hits[0].status, "compiled")
        self.assertTrue(any(hit.kind == "manual" and "243" in hit.pages for hit in hits))

    def test_exact_library_search_finds_official_fit_section(self) -> None:
        hits = search("fit group", limit=8)
        self.assertEqual(hits[0].id, "fit-groups")
        self.assertTrue(
            any(hit.kind == "manual" and hit.pages == "685-687" for hit in hits),
            [hit.__dict__ for hit in hits],
        )

    def test_manual_source_manifest_matches_generated_corpus(self) -> None:
        source = json.loads(
            (
                PROJECT_ROOT
                / "sources/official/pgf/derived/pdf-index/source.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(source["version"], "3.1.11a")
        self.assertEqual(source["page_count"], 1323)
        corpus = PROJECT_ROOT / "knowledge/manual-index/pgfmanual-3.1.11a.jsonl"
        lines = [line for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 800)
        first = json.loads(lines[0])
        last = json.loads(lines[-1])
        self.assertEqual(first["source_id"], source["source_id"])
        self.assertEqual(first["page_start"], 1)
        self.assertEqual(last["page_end"], 1323)

        library_index = json.loads(
            (
                PROJECT_ROOT
                / "knowledge/manual-index/pgfmanual-3.1.11a.libraries.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(library_index["source_id"], source["source_id"])
        libraries = {item["library"]: item for item in library_index["libraries"]}
        for library in ("arrows", "automata", "calc", "fit", "matrix", "positioning", "shapes.geometric"):
            self.assertIn(library, libraries)
            self.assertTrue(libraries[library]["chunk_ids"])
            self.assertTrue(libraries[library]["pages"])

    def test_source_example_corpus_matches_pinned_pgf_source(self) -> None:
        index = json.loads(
            (PROJECT_ROOT / "knowledge/corpus/index.json").read_text(encoding="utf-8")
        )
        self.assertEqual(index["total_examples"], 2857)
        self.assertEqual(index["renderable_examples"], 2358)
        self.assertEqual(len(index["compile_sample_ids"]), 6)
        self.assertEqual(index["verification"]["source-compiled"], 6)
        self.assertEqual(index["compile_status"]["passed"], 6)
        lines = [
            line
            for line in (PROJECT_ROOT / "knowledge/corpus/examples.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), index["total_examples"])
        first = json.loads(lines[0])
        last = json.loads(lines[-1])
        for entry in (first, last):
            self.assertEqual(entry["source_id"], "pgf-manual-source")
            self.assertEqual(entry["source_version"], "3.1.11a")
            self.assertEqual(len(entry["source_hash"]), 64)
            self.assertEqual(len(entry["code_hash"]), 64)
            self.assertIn("doc/generic/pgf/", entry["source_locator"]["path"])

    def test_source_example_corpus_verify_command(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/build_source_example_corpus.py", "verify"],
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("examples=2857", result.stdout)
        self.assertIn("renderable=2358", result.stdout)

    def test_pgfplots_source_example_corpus_matches_pinned_source(self) -> None:
        index = json.loads(
            (
                PROJECT_ROOT
                / "knowledge/corpus/pgfplots-1.18.2.index.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(index["total_examples"], 1290)
        self.assertEqual(index["renderable_examples"], 956)
        self.assertEqual(len(index["compile_sample_ids"]), 6)
        self.assertEqual(index["verification"]["source-compiled"], 6)
        self.assertEqual(index["compile_status"]["passed"], 6)
        lines = [
            line
            for line in (
                PROJECT_ROOT / "knowledge/corpus/pgfplots-1.18.2.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), index["total_examples"])
        sample = json.loads(lines[0])
        self.assertEqual(sample["source_id"], "pgfplots-manual-source")
        self.assertEqual(sample["source_version"], "1.18.2")
        self.assertIn("doc/latex/pgfplots/", sample["source_locator"]["path"])
        sources = json.loads(
            (PROJECT_ROOT / "knowledge/corpus/sources.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {item["id"] for item in sources["sources"]},
            {"pgf-manual-source", "pgfplots-manual-source"},
        )

    def test_unified_knowledge_query_benchmark(self) -> None:
        fixture = json.loads(
            (PROJECT_ROOT / "tests/fixtures/kb-queries.json").read_text(encoding="utf-8")
        )
        for case in fixture["queries"]:
            with self.subTest(query=case["query"]):
                hits = search(case["query"], limit=12)
                self.assertTrue(hits)
                ids = {hit.id for hit in hits}
                kinds = {hit.kind for hit in hits}
                if case.get("top_id"):
                    self.assertEqual(hits[0].id, case["top_id"], [hit.__dict__ for hit in hits])
                for expected_id in case.get("required_ids", []):
                    self.assertIn(expected_id, ids, [hit.__dict__ for hit in hits])
                for expected_kind in case.get("required_kinds", []):
                    self.assertIn(expected_kind, kinds, [hit.__dict__ for hit in hits])

    def test_knowledge_status_includes_recipes_and_source_examples(self) -> None:
        payload = status()
        self.assertEqual(payload["source_examples"], 4147)
        self.assertEqual(payload["recipes"], 19)
        self.assertEqual(payload["templates"], 5)
        self.assertEqual(payload["example_verification"]["source-compiled"], 12)

    @unittest.skipUnless(
        shutil.which("pdftotext") and shutil.which("pdfinfo"),
        "Poppler tools unavailable",
    )
    def test_manual_reference_verify_command(self) -> None:
        result = subprocess.run(
            ["python3", "scripts/build_manual_reference.py", "verify"],
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("pages=1323", result.stdout)

    @unittest.skipUnless(
        shutil.which("latexmk") and shutil.which("pdflatex"),
        "TeX toolchain unavailable",
    )
    def test_portable_plugin_runs_without_source_checkout(self) -> None:
        plugin = PROJECT_ROOT / "packages/plugin/tikz-funfig"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable = root / "tikz-funfig"
            shutil.copytree(plugin, portable)
            wrapper = portable / "skills/funfig-flowcharts/scripts/funfig.sh"
            search_result = subprocess.run(
                ["bash", str(wrapper), "kb", "search", "fit group", "--limit", "2"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(search_result.returncode, 0, search_result.stdout)
            self.assertIn("fit-groups", search_result.stdout)
            pgfplots_search = subprocess.run(
                ["bash", str(wrapper), "kb", "search", "boxplot prepared", "--limit", "2"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(pgfplots_search.returncode, 0, pgfplots_search.stdout)
            self.assertIn("pgfplots-libs.statistics", pgfplots_search.stdout)
            figure = root / "figure"
            init = subprocess.run(
                ["bash", str(wrapper), "init", str(figure), "--recipe", "flowchart", "--id", "portable"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stdout)
            build = subprocess.run(
                ["bash", str(wrapper), "build", str(figure / "figure.funfig.json")],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(build.returncode, 0, build.stdout)
            self.assertTrue((figure / "figure.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
