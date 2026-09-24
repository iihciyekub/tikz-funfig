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
        self.assertEqual(payload["cards"], 36)
        self.assertEqual(payload["manual_chunks"], 1259)
        self.assertEqual(payload["verification"]["compiled"], 36)
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
        self.assertEqual(len(index["compile_sample_ids"]), 11)
        self.assertEqual(index["verification"]["source-compiled"], 11)
        self.assertEqual(index["compile_status"]["passed"], 11)
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
            {
                "pgf-manual-source",
                "pgfplots-manual-source",
                "opentikz-content",
                "janosh-diagrams",
                "petarv-tikz",
            },
        )

    def test_pgfplots_manual_corpus_matches_pinned_tex_source(self) -> None:
        source = json.loads(
            (
                PROJECT_ROOT / "sources/official/pgfplots/source.json"
            ).read_text(encoding="utf-8")
        )
        corpus = PROJECT_ROOT / "knowledge/manual-index/pgfplots-1.18.2.jsonl"
        lines = [
            json.loads(line)
            for line in corpus.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 415)
        self.assertEqual({item["source_id"] for item in lines}, {source["source_id"]})
        self.assertEqual({item["source_version"] for item in lines}, {source["version"]})
        self.assertTrue(any(item["title"] == "Error Bars" for item in lines))
        point_meta = next(
            item for item in lines if item["title"] == "User Input Format for Point Meta"
        )
        self.assertIn("point meta", point_meta["keys"])
        error_bars = next(item for item in lines if item["title"] == "Error Bars")
        self.assertIn("error bars/error mark", error_bars["keys"])
        self.assertTrue(
            all(item["source_file"].startswith("doc/latex/pgfplots/") for item in lines)
        )

        topics = json.loads(
            (
                PROJECT_ROOT / "knowledge/manual-index/pgfplots-1.18.2.topics.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(topics["total_chunks"], 415)
        topic_names = {item["topic"] for item in topics["topics"]}
        for name in ("error-bars", "groupplots", "statistics", "polar", "ternary"):
            self.assertIn(name, topic_names)

    def test_pgfplots_manual_and_curated_layers_are_retrievable(self) -> None:
        hits = search("误差棒", limit=10)
        self.assertEqual(hits[0].id, "pgfplots-error-bars")
        self.assertTrue(any(hit.kind == "template" and hit.id == "error-bars" for hit in hits))
        self.assertTrue(any(hit.kind == "recipe" and hit.id == "error-bar" for hit in hits))
        self.assertTrue(
            any(
                hit.kind == "manual"
                and "pgfplots-reference-errorbars" in hit.id
                for hit in hits
            ),
            [hit.__dict__ for hit in hits],
        )

    def test_community_source_corpus_matches_pinned_snapshots(self) -> None:
        index = json.loads(
            (PROJECT_ROOT / "knowledge/corpus/community.index.json").read_text(encoding="utf-8")
        )
        self.assertEqual(index["total_examples"], 157)
        self.assertEqual(
            index["source_counts"],
            {
                "janosh-diagrams": 80,
                "opentikz-content": 12,
                "petarv-tikz": 65,
            },
        )
        self.assertEqual(index["safety_flagged_examples"], 0)
        self.assertEqual(index["compile_status"]["passed"], 3)
        self.assertEqual(index["verification"]["source-compiled"], 3)
        lines = [
            json.loads(line)
            for line in (PROJECT_ROOT / "knowledge/corpus/community.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(lines), 157)
        self.assertEqual(
            {item["source_id"] for item in lines},
            {"opentikz-content", "janosh-diagrams", "petarv-tikz"},
        )
        self.assertTrue(all(item["source_kind"] == "community" for item in lines))
        self.assertTrue(all(len(item["source_hash"]) == 64 for item in lines))
        self.assertTrue(all(len(item["code_hash"]) == 64 for item in lines))

    def test_community_corpus_is_searchable_without_raw_source_access(self) -> None:
        hits = search("encoder decoder architecture", limit=12)
        self.assertTrue(
            any(
                hit.kind == "example"
                and "encoder-decoder" in hit.source.casefold()
                for hit in hits
            ),
            [hit.__dict__ for hit in hits],
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
        self.assertEqual(payload["source_examples"], 4304)
        self.assertEqual(payload["recipes"], 19)
        self.assertEqual(payload["templates"], 10)
        self.assertEqual(payload["example_verification"]["source-compiled"], 20)

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
            pgfplots_manual_search = subprocess.run(
                [
                    "bash",
                    str(wrapper),
                    "kb",
                    "search",
                    "Error Bars explicit uncertainty",
                    "--limit",
                    "8",
                ],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(
                pgfplots_manual_search.returncode,
                0,
                pgfplots_manual_search.stdout,
            )
            self.assertIn(
                "pgfplots-manual-pgfplots-reference-errorbars",
                pgfplots_manual_search.stdout,
            )
            community_search = subprocess.run(
                [
                    "bash",
                    str(wrapper),
                    "kb",
                    "search",
                    "encoder decoder architecture",
                    "--limit",
                    "5",
                ],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(community_search.returncode, 0, community_search.stdout)
            self.assertIn("opentikz-content", community_search.stdout)
            template_inspect = subprocess.run(
                [
                    "bash",
                    str(wrapper),
                    "templates",
                    "inspect",
                    "layered-framework",
                ],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(template_inspect.returncode, 0, template_inspect.stdout)
            self.assertIn('"id": "layered-framework"', template_inspect.stdout)
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
