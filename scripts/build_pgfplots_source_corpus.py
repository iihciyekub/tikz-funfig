#!/usr/bin/env python3
"""Build the normalized PGFPlots 1.18.2 source-example corpus."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import build_source_example_corpus as common


ROOT = common.ROOT
SOURCE_MANIFEST = ROOT / "sources/official/pgfplots/source.json"
CORPUS_DIR = ROOT / "knowledge/corpus"
EXAMPLES_FILE = CORPUS_DIR / "pgfplots-1.18.2.jsonl"
INDEX_FILE = CORPUS_DIR / "pgfplots-1.18.2.index.json"

SAMPLE_SOURCE_ORDER = (
    "pgfplots.reference.2dplots.tex",
    "pgfplots.reference.errorbars.tex",
    "pgfplots.libs.fillbetween.tex",
    "pgfplots.libs.groupplots.tex",
    "pgfplots.reference.3dplots.tex",
    "pgfplots.libs.statistics.tex",
)

EXTERNAL_DATA_RE = re.compile(
    r"(?:plotdata/|\\addplot\s+file\b|\.(?:dat|csv)\b)",
    flags=re.IGNORECASE,
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _source_root(manifest: dict[str, Any]) -> Path:
    return ROOT / manifest["source_root"]


def _canonical_snapshot_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.name == ".DS_Store":
            continue
        if "gnuplot" in relative.parts:
            continue
        if path.suffix.casefold() in {".png", ".pdf", ".gnuplot"}:
            continue
        files.append(path)
    return sorted(files)


def _canonical_tree_sha256(root: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    for path in _canonical_snapshot_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(bytes.fromhex(common._sha256_file(path)))
        digest.update(b"\0")
    return digest.hexdigest()


def _extra_safety_flags(code: str) -> list[str]:
    flags: set[str] = set()
    if EXTERNAL_DATA_RE.search(code):
        flags.add("external-data")
    if "gnuplot" in code.casefold():
        flags.add("pgfplots-external-compute")
    return sorted(flags)


def build_entries() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _load_json(SOURCE_MANIFEST)
    source_root = _source_root(manifest)
    if not source_root.is_dir():
        raise RuntimeError(f"PGFPlots source root is missing: {source_root}")
    actual_hash = _canonical_tree_sha256(source_root)
    if actual_hash != manifest["tree_sha256"]:
        raise RuntimeError(
            "PGFPlots source tree hash mismatch: "
            f"expected {manifest['tree_sha256']}, got {actual_hash}"
        )
    tex_files = sorted(source_root.rglob("*.tex"))
    if len(tex_files) != manifest["tex_file_count"]:
        raise RuntimeError(
            "PGFPlots source TeX count mismatch: "
            f"expected {manifest['tex_file_count']}, got {len(tex_files)}"
        )
    entries: list[dict[str, Any]] = []
    for path in tex_files:
        extracted = common._extract_file(
            path,
            source_root,
            manifest["source_id"],
            manifest["version"],
            locator_prefix="doc/latex/pgfplots",
            id_prefix="pgfplots",
            license_ids=manifest["license_ids"],
        )
        for entry in extracted:
            entry["summary"] = (
                f"Official PGFPlots code example from {entry['title']}."
            )
            entry["packages"] = sorted(set([*entry.get("packages", []), "pgfplots"]))
            entry["tags"] = sorted(set([*entry.get("tags", []), "pgfplots"]))
            entry["figure_families"] = sorted(
                set([*entry.get("figure_families", []), "plot"])
            )
            extra_flags = _extra_safety_flags(
                "\n".join(
                    [
                        entry.get("preamble", ""),
                        entry.get("setup_code", ""),
                        entry.get("pre", ""),
                        entry.get("render_instead") or entry.get("code", ""),
                        entry.get("post", ""),
                    ]
                )
            )
            entry["safety_flags"] = sorted(
                set([*entry.get("safety_flags", []), *extra_flags])
            )
            entry["compile_eligible"] = bool(entry["renderable"]) and not entry["safety_flags"]
        entries.extend(extracted)
    return manifest, entries


def _sample_ids(entries: list[dict[str, Any]]) -> list[str]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        name = Path(entry["source_locator"]["path"]).name
        by_name.setdefault(name, []).append(entry)
    result: list[str] = []
    for source_name in SAMPLE_SOURCE_ORDER:
        for entry in by_name.get(source_name, []):
            code = entry.get("render_instead") or entry.get("code", "")
            if (
                entry["compile_eligible"]
                and entry["engine"] == "pdflatex"
                and "\\begin{axis}" in code
            ):
                result.append(entry["id"])
                break
    return result


def _index_payload(manifest: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    skip_counts = Counter(entry["skip_reason"] or "none" for entry in entries)
    verification_counts = Counter(entry["verification"] for entry in entries)
    compile_counts = Counter(entry["compile_status"] for entry in entries)
    library_counts = Counter(
        library for entry in entries for library in entry.get("libraries", [])
    )
    return {
        "schema_version": "1.0",
        "kind": "source-example-corpus",
        "sources": [manifest["source_id"]],
        "total_examples": len(entries),
        "renderable_examples": sum(bool(entry["renderable"]) for entry in entries),
        "compile_eligible_examples": sum(
            bool(entry["compile_eligible"]) for entry in entries
        ),
        "safety_flagged_examples": sum(bool(entry["safety_flags"]) for entry in entries),
        "skip_reasons": dict(sorted(skip_counts.items())),
        "verification": dict(sorted(verification_counts.items())),
        "compile_status": dict(sorted(compile_counts.items())),
        "top_libraries": dict(library_counts.most_common(40)),
        "compile_sample_ids": _sample_ids(entries),
        "examples_file": EXAMPLES_FILE.name,
    }


def _standalone_source(entry: dict[str, Any]) -> str:
    code = entry["render_instead"] or entry["code"]
    typed = entry.get("library_types", {})
    library_lines: list[str] = []
    if typed.get("tikz"):
        library_lines.append(
            "\\usetikzlibrary{" + ",".join(typed["tikz"]) + "}"
        )
    if typed.get("pgf"):
        library_lines.append(
            "\\usepgflibrary{" + ",".join(typed["pgf"]) + "}"
        )
    if typed.get("pgfplots"):
        library_lines.append(
            "\\usepgfplotslibrary{" + ",".join(typed["pgfplots"]) + "}"
        )
    return (
        "\\documentclass{standalone}\n"
        "\\usepackage[dvipsnames,svgnames,x11names]{xcolor}\n"
        "\\usepackage{tikz}\n"
        "\\usepackage{pgfplots}\n"
        "\\pgfplotsset{compat=1.18}\n"
        + "\n".join(library_lines)
        + "\n"
        f"{entry['preamble']}\n"
        "\\begin{document}\n"
        f"{entry['setup_code']}\n"
        f"{entry['pre']}\n"
        f"{code}\n"
        f"{entry['post']}\n"
        "\\end{document}\n"
    )


def _compile_samples(entries: list[dict[str, Any]], sample_ids: list[str]) -> None:
    if not sample_ids:
        raise RuntimeError("no PGFPlots compile sample IDs resolved")
    entry_by_id = {entry["id"]: entry for entry in entries}
    with tempfile.TemporaryDirectory(prefix="tff-pgfplots-corpus-") as temp:
        root = Path(temp)
        for example_id in sample_ids:
            entry = entry_by_id[example_id]
            if not shutil.which("pdflatex"):
                raise RuntimeError("missing pdflatex for PGFPlots corpus verification")
            example_dir = root / example_id
            example_dir.mkdir()
            tex = example_dir / "example.tex"
            tex.write_text(_standalone_source(entry), encoding="utf-8")
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(example_dir),
                    str(tex),
                ],
                cwd=example_dir,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if result.returncode or not (example_dir / "example.pdf").is_file():
                tail = "\n".join(result.stdout.splitlines()[-35:])
                raise RuntimeError(f"compile failed for {example_id}:\n{tail}")


def build(write: bool = True) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    manifest, entries = build_entries()
    verified_ids = set(_sample_ids(entries))
    for entry in entries:
        if entry["id"] in verified_ids:
            entry["verification"] = "source-compiled"
            entry["compile_status"] = "passed"
    jsonl = common._jsonl(entries)
    if write:
        CORPUS_DIR.mkdir(parents=True, exist_ok=True)
        EXAMPLES_FILE.write_text(jsonl, encoding="utf-8")
        _dump_json(INDEX_FILE, _index_payload(manifest, entries))
        common._dump_json(
            common.SOURCES_FILE,
            common._runtime_sources_payload(manifest),
        )
    return manifest, entries, jsonl


def verify(compile_samples: bool) -> None:
    manifest, entries, expected_jsonl = build(write=False)
    expected_index = json.dumps(
        _index_payload(manifest, entries),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    expected_sources = json.dumps(
        common._runtime_sources_payload(manifest),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    expected = {
        EXAMPLES_FILE: expected_jsonl,
        INDEX_FILE: expected_index,
        common.SOURCES_FILE: expected_sources,
    }
    for path, content in expected.items():
        if not path.is_file():
            raise RuntimeError(f"missing generated PGFPlots corpus file: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"generated PGFPlots corpus is stale: {path}")
    source_root = _source_root(manifest)
    source_count = 0
    for path in source_root.rglob("*.tex"):
        text = path.read_text(encoding="utf-8")
        source_count += sum(
            not common._is_commented(text, match.start())
            for match in common.BEGIN_RE.finditer(text)
        )
    if source_count != len(entries):
        raise RuntimeError(
            f"PGFPlots codeexample count mismatch: source={source_count}, corpus={len(entries)}"
        )
    samples = _sample_ids(entries)
    if compile_samples:
        _compile_samples(entries, samples)
    print(
        "ok: pgfplots source-example corpus "
        f"examples={len(entries)} "
        f"renderable={sum(bool(e['renderable']) for e in entries)} "
        f"safety_flagged={sum(bool(e['safety_flags']) for e in entries)} "
        f"compile_samples={len(samples) if compile_samples else 0}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--compile-samples", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "build":
        manifest, entries, _ = build(write=True)
        print(
            f"ok: wrote {len(entries)} examples from PGFPlots {manifest['version']} "
            f"to {EXAMPLES_FILE.relative_to(ROOT)}"
        )
        return 0
    verify(args.compile_samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
