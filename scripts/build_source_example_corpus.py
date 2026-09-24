#!/usr/bin/env python3
"""Build the normalized PGF/TikZ source-example corpus.

This importer deliberately uses only Python's standard library. The pinned
upstream PGF documentation source is development input; generated JSONL under
knowledge/corpus is the runtime-searchable representation.

The official PGF extract.lua remains an upstream behavior reference. This
script additionally records source locations, section context, safety flags,
libraries, commands, layout hints, hashes, and deterministic sample IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "sources/official/pgf/source.json"
SOURCE_REGISTRY = ROOT / "sources/registry.json"
CORPUS_DIR = ROOT / "knowledge/corpus"
EXAMPLES_FILE = CORPUS_DIR / "examples.jsonl"
INDEX_FILE = CORPUS_DIR / "index.json"
SOURCES_FILE = CORPUS_DIR / "sources.json"

BEGIN = r"\begin{codeexample}"
END = r"\end{codeexample}"
BEGIN_RE = re.compile(re.escape(BEGIN))
SECTION_RE = re.compile(
    r"\\(chapter|section|subsection|subsubsection|paragraph)\s*\{",
    flags=re.MULTILINE,
)
COMMAND_RE = re.compile(r"\\[A-Za-z@]+")
KEY_RE = re.compile(r"/(?:tikz|pgf|pgfplots)/[A-Za-z0-9 ._:/-]+")
TIKZ_LIBRARY_RE = re.compile(r"\\usetikzlibrary\s*\{([^}]*)\}")
PGF_LIBRARY_RE = re.compile(r"\\usepgflibrary\s*\{([^}]*)\}")
PGFPLOTS_LIBRARY_RE = re.compile(r"\\usepgfplotslibrary\s*\{([^}]*)\}")
PGFPLOTS_LIBRARY_ENV_RE = re.compile(
    r"\\begin\{pgfplotslibrary\}\s*\{([^}]*)\}"
)
PACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\s*\{([^}]*)\}")

SECTION_LEVELS = {
    "chapter": 0,
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
    "paragraph": 4,
}

SAMPLE_SOURCE_ORDER = (
    "pgfmanual-en-tikz-shapes.tex",
    "pgfmanual-en-library-fit.tex",
    "pgfmanual-en-library-backgrounds.tex",
    "pgfmanual-en-library-chains.tex",
    "pgfmanual-en-tikz-arrows.tex",
    "pgfmanual-en-tikz-paths.tex",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(bytes.fromhex(_sha256_file(path)))
        digest.update(b"\0")
    return digest.hexdigest()


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _is_commented(text: str, position: int) -> bool:
    line_start = text.rfind("\n", 0, position) + 1
    cursor = line_start
    while cursor < position:
        if text[cursor] == "%" and not _is_escaped(text, cursor):
            return True
        cursor += 1
    return False


def _read_balanced_braces(text: str, open_index: int) -> tuple[str, int]:
    if open_index >= len(text) or text[open_index] != "{":
        raise ValueError("expected opening brace")
    depth = 1
    cursor = open_index + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "{" and not _is_escaped(text, cursor):
            depth += 1
        elif char == "}" and not _is_escaped(text, cursor):
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : cursor], cursor + 1
        cursor += 1
    raise ValueError("unterminated brace group")


def _read_option_block(text: str, open_index: int) -> tuple[str, int]:
    if open_index >= len(text) or text[open_index] != "[":
        return "", open_index
    square_depth = 1
    brace_depth = 0
    cursor = open_index + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "{" and not _is_escaped(text, cursor):
            brace_depth += 1
        elif char == "}" and not _is_escaped(text, cursor) and brace_depth:
            brace_depth -= 1
        elif brace_depth == 0 and char == "[" and not _is_escaped(text, cursor):
            square_depth += 1
        elif brace_depth == 0 and char == "]" and not _is_escaped(text, cursor):
            square_depth -= 1
            if square_depth == 0:
                return text[open_index + 1 : cursor], cursor + 1
        cursor += 1
    raise ValueError("unterminated codeexample option block")


def _split_top_level(text: str, delimiter: str) -> list[str]:
    result: list[str] = []
    start = 0
    brace_depth = 0
    square_depth = 0
    for index, char in enumerate(text):
        if char == "{" and not _is_escaped(text, index):
            brace_depth += 1
        elif char == "}" and not _is_escaped(text, index) and brace_depth:
            brace_depth -= 1
        elif char == "[" and not _is_escaped(text, index):
            square_depth += 1
        elif char == "]" and not _is_escaped(text, index) and square_depth:
            square_depth -= 1
        elif char == delimiter and brace_depth == 0 and square_depth == 0:
            result.append(text[start:index])
            start = index + 1
    result.append(text[start:])
    return result


def _strip_outer_braces(value: str) -> str:
    value = value.strip()
    if len(value) < 2 or not (value.startswith("{") and value.endswith("}")):
        return value
    try:
        body, end = _read_balanced_braces(value, 0)
    except ValueError:
        return value
    return body if end == len(value) else value


def _parse_options(raw: str) -> dict[str, str | bool]:
    options: dict[str, str | bool] = {}
    for item in _split_top_level(raw, ","):
        item = item.strip()
        if not item:
            continue
        pieces = _split_top_level(item, "=")
        if len(pieces) == 1:
            options[item] = True
            continue
        key = pieces[0].strip()
        value = "=".join(pieces[1:]).strip()
        options[key] = _strip_outer_braces(value)
    return options


def _plain_tex(value: str) -> str:
    value = re.sub(
        r"\\(?:texttt|textbf|emph|tikzname|pgfname)\s*\{([^{}]*)\}",
        r"\1",
        value,
    )
    value = re.sub(r"\\[A-Za-z@]+\*?", "", value)
    value = value.replace("{", "").replace("}", "")
    value = value.replace("|", "")
    return re.sub(r"\s+", " ", value).strip()


def _section_events(text: str) -> list[tuple[int, int, str, str]]:
    events: list[tuple[int, int, str, str]] = []
    for match in SECTION_RE.finditer(text):
        if _is_commented(text, match.start()):
            continue
        command = match.group(1)
        open_brace = match.end() - 1
        try:
            raw_title, _ = _read_balanced_braces(text, open_brace)
        except ValueError:
            continue
        events.append(
            (match.start(), SECTION_LEVELS[command], command, _plain_tex(raw_title))
        )
    return events


def _libraries(*chunks: str) -> list[str]:
    typed = _typed_libraries(*chunks)
    return sorted(
        set(
            [
                *typed["tikz"],
                *typed["pgf"],
                *typed["pgfplots"],
            ]
        )
    )


def _typed_libraries(*chunks: str) -> dict[str, list[str]]:
    result: dict[str, set[str]] = {
        "tikz": set(),
        "pgf": set(),
        "pgfplots": set(),
    }
    for text in chunks:
        for kind, pattern in (
            ("tikz", TIKZ_LIBRARY_RE),
            ("pgf", PGF_LIBRARY_RE),
            ("pgfplots", PGFPLOTS_LIBRARY_RE),
            ("pgfplots", PGFPLOTS_LIBRARY_ENV_RE),
        ):
            for raw in pattern.findall(text):
                result[kind].update(
                    value.strip() for value in raw.split(",") if value.strip()
                )
    return {kind: sorted(values) for kind, values in result.items()}


def _packages(*chunks: str) -> list[str]:
    result = {"fp", "pgf", "tikz", "xcolor"}
    for text in chunks:
        for raw in PACKAGE_RE.findall(text):
            result.update(value.strip() for value in raw.split(",") if value.strip())
    return sorted(result)


def _commands(*chunks: str) -> list[str]:
    return sorted(set(COMMAND_RE.findall("\n".join(chunks))))[:160]


def _keys(*chunks: str) -> list[str]:
    values = (value.rstrip(" .,:;") for value in KEY_RE.findall("\n".join(chunks)))
    return sorted(set(values))[:160]


def _safety_flags(text: str) -> list[str]:
    patterns = {
        "shell-escape": r"\\(?:immediate\s*)?write18\b",
        "open-input": r"\\openin\b",
        "open-output": r"\\openout\b",
        "input-file": r"\\(?:input|include)\b",
        "external-file": r"\\includegraphics(?:\[[^\]]*\])?\s*\{",
        "direct-lua": r"\\directlua\b",
        "external-program": r"\\(?:pgfplotgnuplot|write18)\b",
    }
    return sorted(name for name, pattern in patterns.items() if re.search(pattern, text))


def _figure_families(
    source_name: str,
    title: str,
    libraries: list[str],
    code: str,
) -> list[str]:
    haystack = " ".join([source_name, title, " ".join(libraries), code[:1800]]).casefold()
    result: set[str] = set()
    if any(token in haystack for token in ("datavisualization", "plot", "axis")):
        result.add("plot")
    if any(token in haystack for token in ("automata", "state ")):
        result.add("state")
    if any(token in haystack for token in ("tree", "phylogen")):
        result.add("tree")
    if any(token in haystack for token in ("graphdrawing", "graph drawing", "\\graph")):
        result.update(("graph", "relation"))
    if any(token in haystack for token in ("circuit", "perspective", "3d")):
        result.add("schematic")
    if any(token in haystack for token in ("fit", "backgrounds", "matrix", "chains", "positioning")):
        result.add("framework")
    if any(token in haystack for token in ("edge", "arrow", "node")):
        result.add("relation")
    if any(token in haystack for token in ("angle", "coordinate", "calc", "intersection")):
        result.add("geometry")
    return sorted(result or {"tikz"})


def _layout_traits(source_name: str, title: str, libraries: list[str], code: str) -> list[str]:
    haystack = " ".join([source_name, title, " ".join(libraries), code[:1400]]).casefold()
    result: set[str] = set()
    if "positioning" in haystack or any(token in code for token in ("right=", "left=", "above=", "below=")):
        result.add("relative")
    if "matrix" in haystack:
        result.add("grid")
    if "fit" in haystack or "backgrounds" in haystack:
        result.add("grouped")
    if "layered" in haystack:
        result.add("layered")
    if "circular" in haystack:
        result.add("radial")
    if "tree" in haystack:
        result.add("tree")
    return sorted(result)


def _style_traits(libraries: list[str], code: str) -> list[str]:
    haystack = (" ".join(libraries) + " " + code[:1600]).casefold()
    result: set[str] = set()
    if any(token in haystack for token in ("pattern", "shade", "shadow", "fadings")):
        result.add("decorative")
    if any(token in haystack for token in ("gray", "black!", "white")):
        result.add("monochrome-capable")
    if "very thick" not in haystack and "ultra thick" not in haystack:
        result.add("publication-adaptable")
    return sorted(result)


def _engine(libraries: list[str], code: str, preamble: str) -> str:
    haystack = " ".join(libraries) + "\n" + preamble + "\n" + code
    if "graphdrawing" in haystack or "\\usegdlibrary" in haystack or "\\directlua" in haystack:
        return "lualatex"
    return "pdflatex"


def _source_path_for_locator(relative: Path, locator_prefix: str) -> str:
    return f"{locator_prefix.rstrip('/')}/{relative.as_posix()}"


def _extract_file(
    path: Path,
    source_root: Path,
    source_id: str,
    version: str,
    *,
    locator_prefix: str = "doc/generic/pgf",
    id_prefix: str = "pgf",
    license_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")
    relative = path.relative_to(source_root)
    source_sha = _sha256_bytes(raw_bytes)
    sections = _section_events(text)
    file_library_types = _typed_libraries(text)
    section_index = 0
    hierarchy: dict[int, dict[str, Any]] = {}
    examples: list[dict[str, Any]] = []
    setup_code = ""
    ordinal = 0

    for begin_match in BEGIN_RE.finditer(text):
        if _is_commented(text, begin_match.start()):
            continue
        ordinal += 1
        cursor = begin_match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        raw_options, content_start = _read_option_block(text, cursor)
        if content_start == cursor:
            content_start = cursor
        end_index = text.find(END, content_start)
        if end_index < 0:
            raise RuntimeError(f"unterminated codeexample: {relative}:{ordinal}")
        content = text[content_start:end_index].strip()

        while section_index < len(sections) and sections[section_index][0] <= begin_match.start():
            _, level, command, title = sections[section_index]
            hierarchy[level] = {"level": command, "title": title}
            for stale in [value for value in hierarchy if value > level]:
                hierarchy.pop(stale, None)
            section_index += 1
        section_path = [hierarchy[level] for level in sorted(hierarchy)]
        section_title = section_path[-1]["title"] if section_path else relative.stem

        options = _parse_options(raw_options)
        current_setup = setup_code
        is_setup = bool(options.get("setup code"))
        is_code_only = bool(options.get("code only"))
        remember_picture = "remember picture" in content
        preamble = str(options.get("preamble", "") if options.get("preamble") is not True else "")
        pre = str(options.get("pre", "") if options.get("pre") is not True else "").replace("##", "#")
        post = str(options.get("post", "") if options.get("post") is not True else "")
        render_instead = str(
            options.get("render instead", "") if options.get("render instead") is not True else ""
        )
        render_code = render_instead or content
        analysis_text = "\n".join((preamble, current_setup, pre, render_code, post))
        local_library_types = _typed_libraries(analysis_text)
        library_types = {
            kind: sorted(
                set(
                    [
                        *file_library_types.get(kind, []),
                        *local_library_types.get(kind, []),
                    ]
                )
            )
            for kind in ("tikz", "pgf", "pgfplots")
        }
        libraries = sorted(
            set(
                [
                    *library_types["tikz"],
                    *library_types["pgf"],
                    *library_types["pgfplots"],
                ]
            )
        )
        safety = _safety_flags(analysis_text)
        renderable = not is_setup and not is_code_only and not remember_picture
        compile_eligible = renderable and not safety
        engine = _engine(libraries, render_code, preamble)
        stem = relative.stem
        for prefix in ("pgfmanual-en-", "pgfplots."):
            if stem.startswith(prefix):
                stem = stem[len(prefix) :]
        example_id = f"{id_prefix}-{stem}-{ordinal:04d}"
        line_start = text.count("\n", 0, begin_match.start()) + 1
        line_end = text.count("\n", 0, end_index + len(END)) + 1

        examples.append(
            {
                "id": example_id,
                "source_id": source_id,
                "source_kind": "official",
                "source_version": version,
                "source_locator": {
                    "path": _source_path_for_locator(relative, locator_prefix),
                    "line_start": line_start,
                    "line_end": line_end,
                    "ordinal": ordinal,
                    "section_path": section_path,
                },
                "title": section_title,
                "summary": f"Official PGF/TikZ code example from {section_title}.",
                "figure_families": _figure_families(relative.name, section_title, libraries, render_code),
                "layout_traits": _layout_traits(relative.name, section_title, libraries, render_code),
                "style_traits": _style_traits(libraries, render_code),
                "tags": sorted(
                    set(
                        [
                            relative.stem.removeprefix("pgfmanual-en-").replace("-", " "),
                            *(item["title"] for item in section_path),
                        ]
                    )
                ),
                "libraries": libraries,
                "library_types": library_types,
                "packages": _packages(preamble, current_setup),
                "commands": _commands(preamble, current_setup, pre, render_code, post),
                "keys": _keys(preamble, current_setup, pre, render_code, post),
                "engine": engine,
                "options": options,
                "code": content,
                "setup_code": current_setup,
                "preamble": preamble,
                "pre": pre,
                "post": post,
                "render_instead": render_instead,
                "renderable": renderable,
                "compile_eligible": compile_eligible,
                "safety_flags": safety,
                "skip_reason": (
                    "setup-code"
                    if is_setup
                    else "code-only"
                    if is_code_only
                    else "remember-picture"
                    if remember_picture
                    else None
                ),
                "verification": "source-extracted",
                "compile_status": "not-run",
                "license_ids": license_ids or ["LPPL-1.3c", "GFDL-1.2"],
                "source_hash": source_sha,
                "code_hash": _sha256_bytes(content.encode("utf-8")),
            }
        )
        if is_setup:
            setup_code += content.strip() + "\n"
    return examples


def _source_root(manifest: dict[str, Any]) -> Path:
    return ROOT / manifest["source_root"]


def build_entries() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _load_json(SOURCE_MANIFEST)
    source_root = _source_root(manifest)
    if not source_root.is_dir():
        raise RuntimeError(f"PGF source root is missing: {source_root}")
    actual_tree_hash = _tree_sha256(source_root)
    if actual_tree_hash != manifest["tree_sha256"]:
        raise RuntimeError(
            f"PGF source tree hash mismatch: expected {manifest['tree_sha256']}, got {actual_tree_hash}"
        )
    tex_files = sorted(source_root.rglob("*.tex"))
    if len(tex_files) != manifest["tex_file_count"]:
        raise RuntimeError(
            f"PGF source TeX count mismatch: expected {manifest['tex_file_count']}, got {len(tex_files)}"
        )
    entries: list[dict[str, Any]] = []
    for path in tex_files:
        entries.extend(
            _extract_file(path, source_root, manifest["source_id"], manifest["version"])
        )
    return manifest, entries


def _sample_ids(entries: list[dict[str, Any]]) -> list[str]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        name = Path(entry["source_locator"]["path"]).name
        by_name.setdefault(name, []).append(entry)
    result: list[str] = []
    for source_name in SAMPLE_SOURCE_ORDER:
        for entry in by_name.get(source_name, []):
            if entry["compile_eligible"] and entry["engine"] == "pdflatex":
                result.append(entry["id"])
                break
    return result


def _index_payload(manifest: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    skip_counts = Counter(entry["skip_reason"] or "none" for entry in entries)
    verification_counts = Counter(entry["verification"] for entry in entries)
    compile_counts = Counter(entry["compile_status"] for entry in entries)
    family_counts = Counter(
        family for entry in entries for family in entry.get("figure_families", [])
    )
    library_counts = Counter(
        library for entry in entries for library in entry.get("libraries", [])
    )
    return {
        "schema_version": "1.0",
        "kind": "source-example-corpus",
        "sources": [manifest["source_id"]],
        "total_examples": len(entries),
        "renderable_examples": sum(bool(entry["renderable"]) for entry in entries),
        "compile_eligible_examples": sum(bool(entry["compile_eligible"]) for entry in entries),
        "safety_flagged_examples": sum(bool(entry["safety_flags"]) for entry in entries),
        "skip_reasons": dict(sorted(skip_counts.items())),
        "verification": dict(sorted(verification_counts.items())),
        "compile_status": dict(sorted(compile_counts.items())),
        "figure_families": dict(sorted(family_counts.items())),
        "top_libraries": dict(library_counts.most_common(40)),
        "compile_sample_ids": _sample_ids(entries),
        "examples_file": "examples.jsonl",
        "sources_file": "sources.json",
    }


def _runtime_sources_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    registry = _load_json(SOURCE_REGISTRY)
    sources: list[dict[str, Any]] = []
    for record in registry.get("sources", []):
        if record.get("plugin_policy") != "normalized-only":
            continue
        source_manifest = {}
        manifest_path = record.get("manifest")
        if manifest_path and (ROOT / manifest_path).is_file():
            source_manifest = _load_json(ROOT / manifest_path)
        sources.append(
            {
                "id": record["id"],
                "kind": record["kind"],
                "project": record["project"],
                "upstream": record["upstream"],
                "revision": record["revision"],
                "version": source_manifest.get(
                    "version",
                    record.get("release_tag", record["revision"]),
                ),
                "license_ids": record.get("license_ids", []),
                "plugin_policy": record["plugin_policy"],
            }
        )
    return {
        "schema_version": "1.0",
        "sources": sources,
    }


def _jsonl(entries: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for entry in entries
    )


def build(write: bool = True) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    manifest, entries = build_entries()
    verified_sample_ids = set(_sample_ids(entries))
    for entry in entries:
        if entry["id"] in verified_sample_ids:
            entry["verification"] = "source-compiled"
            entry["compile_status"] = "passed"
    jsonl = _jsonl(entries)
    if write:
        CORPUS_DIR.mkdir(parents=True, exist_ok=True)
        EXAMPLES_FILE.write_text(jsonl, encoding="utf-8")
        _dump_json(INDEX_FILE, _index_payload(manifest, entries))
        _dump_json(SOURCES_FILE, _runtime_sources_payload(manifest))
    return manifest, entries, jsonl


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
        library_lines.extend(
            [
                "\\usepackage{pgfplots}",
                "\\usepgfplotslibrary{" + ",".join(typed["pgfplots"]) + "}",
            ]
        )
    return (
        "\\documentclass{standalone}\n"
        "\\usepackage{fp,pgf,tikz,xcolor}\n"
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
        raise RuntimeError("no compile sample IDs resolved")
    entry_by_id = {entry["id"]: entry for entry in entries}
    with tempfile.TemporaryDirectory(prefix="tff-pgf-corpus-") as temp:
        root = Path(temp)
        for example_id in sample_ids:
            entry = entry_by_id[example_id]
            engine = entry["engine"]
            if not shutil.which(engine):
                raise RuntimeError(f"missing TeX engine for corpus verification: {engine}")
            example_dir = root / example_id
            example_dir.mkdir()
            tex = example_dir / "example.tex"
            tex.write_text(_standalone_source(entry), encoding="utf-8")
            result = subprocess.run(
                [
                    engine,
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
                tail = "\n".join(result.stdout.splitlines()[-30:])
                raise RuntimeError(f"compile failed for {example_id}:\n{tail}")


def _official_renderable_count(manifest: dict[str, Any]) -> int | None:
    texlua = shutil.which("texlua")
    if not texlua:
        return None
    extractor = ROOT / manifest["extractor"]
    source_root = _source_root(manifest)
    if not extractor.is_file():
        raise RuntimeError(f"official PGF extractor is missing: {extractor}")
    with tempfile.TemporaryDirectory(prefix="tff-pgf-official-extract-") as temp:
        result = subprocess.run(
            [texlua, str(extractor), str(source_root), temp],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if result.returncode:
            tail = "\n".join(result.stdout.splitlines()[-30:])
            raise RuntimeError(f"official PGF extractor failed:\n{tail}")
        return len(list(Path(temp).rglob("*.tex")))


def verify(compile_samples: bool) -> None:
    manifest, entries, expected_jsonl = build(write=False)
    expected_index = json.dumps(
        _index_payload(manifest, entries),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    expected_sources = json.dumps(
        _runtime_sources_payload(manifest),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    committed = {
        EXAMPLES_FILE: expected_jsonl,
        INDEX_FILE: expected_index,
        SOURCES_FILE: expected_sources,
    }
    for path, expected in committed.items():
        if not path.is_file():
            raise RuntimeError(f"missing generated corpus file: {path}")
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            raise RuntimeError(f"generated corpus is stale: {path}")
    begin_count = 0
    source_root = _source_root(manifest)
    for path in source_root.rglob("*.tex"):
        text = path.read_text(encoding="utf-8")
        begin_count += sum(
            not _is_commented(text, match.start()) for match in BEGIN_RE.finditer(text)
        )
    if begin_count != len(entries):
        raise RuntimeError(
            f"codeexample count mismatch: source={begin_count}, corpus={len(entries)}"
        )
    official_count = _official_renderable_count(manifest)
    renderable_count = sum(bool(entry["renderable"]) for entry in entries)
    if official_count is not None and official_count != renderable_count:
        raise RuntimeError(
            "official extractor mismatch: "
            f"official={official_count}, importer={renderable_count}"
        )
    samples = _sample_ids(entries)
    if compile_samples:
        _compile_samples(entries, samples)
    print(
        "ok: source-example corpus "
        f"examples={len(entries)} renderable={renderable_count} "
        f"official_renderable={official_count if official_count is not None else 'unavailable'} "
        f"safety_flagged={sum(bool(e['safety_flags']) for e in entries)} "
        f"compile_samples={len(samples) if compile_samples else 0}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="rebuild normalized source-example corpus")
    verify_parser = subparsers.add_parser("verify", help="verify committed corpus is current")
    verify_parser.add_argument(
        "--compile-samples",
        action="store_true",
        help="compile a deterministic representative sample from priority PGF topics",
    )
    args = parser.parse_args(argv)
    if args.command == "build":
        manifest, entries, _ = build(write=True)
        print(
            f"ok: wrote {len(entries)} examples from PGF/TikZ {manifest['version']} "
            f"to {EXAMPLES_FILE.relative_to(ROOT)}"
        )
        return 0
    if args.command == "verify":
        verify(args.compile_samples)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
