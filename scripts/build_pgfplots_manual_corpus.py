#!/usr/bin/env python3
"""Build a searchable PGFPlots manual corpus directly from pinned TeX source."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import build_source_example_corpus as common
import build_pgfplots_source_corpus as pgfplots_examples


ROOT = common.ROOT
SOURCE_MANIFEST = ROOT / "sources/official/pgfplots/source.json"
OUTPUT = ROOT / "knowledge/manual-index/pgfplots-1.18.2.jsonl"
TOPICS = ROOT / "knowledge/manual-index/pgfplots-1.18.2.topics.json"

HEADING_LEVELS = {
    "chapter": 1,
    "section": 2,
    "subsection": 3,
    "subsubsection": 4,
    "paragraph": 5,
}

EVENT_RE = re.compile(
    r"\\(chapter|section|subsection|subsubsection|paragraph|input|include)\s*\{"
)
COMMAND_RE = re.compile(r"\\[A-Za-z@]+")
KEY_RE = re.compile(r"/pgfplots/[A-Za-z0-9 ._:/=-]+")
KEY_ENV_RE = re.compile(
    r"\\begin\{(?:pgfplotskey|pgfplotskeylist|pgfplotsxykeylist|stylekey)\}\s*\{"
)
PGFPLOTS_LIBRARY_RE = re.compile(r"\\usepgfplotslibrary\s*\{([^}]*)\}")
LIBRARY_HINT_RE = re.compile(
    r"\\def\\pgfplotsmanualcurlibrary\s*\{([^}]*)\}"
)
CODEEXAMPLE_RE = re.compile(
    r"\\begin\{codeexample\}.*?\\end\{codeexample\}",
    flags=re.DOTALL,
)
LABEL_RE = re.compile(r"\\label\{[^}]*\}")
INDEX_RE = re.compile(r"\\(?:index|pgfmanualpdflabel)\{[^}]*\}(?:\{[^}]*\})?")
BEGIN_END_RE = re.compile(r"\\(?:begin|end)\{[^}]*\}")
MACRO_RE = re.compile(r"\\[A-Za-z@]+\*?")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _plain_title(value: str) -> str:
    text = value.replace(r"\protect", "")
    text = text.replace(r"\textbackslash", "")
    text = MACRO_RE.sub("", text)
    text = text.replace("{", "").replace("}", "")
    text = text.replace("~", " ").replace("\\", "")
    return re.sub(r"\s+", " ", text).strip()


def _strip_comments(text: str) -> str:
    result: list[str] = []
    for line in text.splitlines():
        cut = len(line)
        for index, char in enumerate(line):
            if char == "%" and not common._is_escaped(line, index):
                cut = index
                break
        result.append(line[:cut])
    return "\n".join(result)


def _plain_body(text: str) -> str:
    text = _strip_comments(text)
    text = CODEEXAMPLE_RE.sub(" ", text)
    text = LABEL_RE.sub(" ", text)
    text = INDEX_RE.sub(" ", text)
    text = BEGIN_END_RE.sub(" ", text)
    text = text.replace(r"\%", "%")
    text = text.replace(r"\_", "_")
    text = text.replace("~", " ")
    text = MACRO_RE.sub(" ", text)
    text = text.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", text).strip()


def _libraries(text: str, file_name: str) -> list[str]:
    values: set[str] = set()
    for raw in PGFPLOTS_LIBRARY_RE.findall(text):
        values.update(part.strip() for part in raw.split(",") if part.strip())
    values.update(value.strip() for value in LIBRARY_HINT_RE.findall(text) if value.strip())
    match = re.match(r"pgfplots\.libs\.([^.]+)\.tex$", file_name)
    if match:
        values.add(match.group(1))
    return sorted(values)


def _declared_keys(text: str) -> list[str]:
    values: set[str] = {
        value.strip().rstrip("= ")
        for value in KEY_RE.findall(text)
        if value.strip()
    }
    for match in KEY_ENV_RE.finditer(text):
        if common._is_commented(text, match.start()):
            continue
        try:
            raw, _ = common._read_balanced_braces(text, match.end() - 1)
        except ValueError:
            continue
        for item in common._split_top_level(raw, ","):
            candidate = item.strip()
            if not candidate:
                continue
            name = common._split_top_level(candidate, "=")[0].strip()
            name = re.sub(r"\\(?:marg|meta|mchoice|texttt)\b.*$", "", name).strip()
            if name:
                values.add(name)
    return sorted(values)


def _topic_ids(title: str, source_file: str, libraries: list[str]) -> list[str]:
    probe = f"{title} {source_file}".casefold()
    topics: set[str] = set(libraries)
    rules = {
        "axis": ("axis", "axes"),
        "2d": ("2d", "two dimensional"),
        "3d": ("3d", "three dimensional", "surface", "mesh"),
        "error-bars": ("error bar",),
        "scatter": ("scatter", "point meta"),
        "table-data": ("table", "coordinate input"),
        "statistics": ("statistics", "histogram", "boxplot"),
        "groupplots": ("group plot", "grouping plots"),
        "fillbetween": ("fill between",),
        "colormap": ("colormap", "colorbar", "colorbrewer"),
        "contour": ("contour",),
        "quiver": ("quiver",),
        "polar": ("polar",),
        "ternary": ("ternary",),
        "filtering": ("filter", "discard"),
        "scaling": ("scaling", "scale"),
        "markers": ("marker", "mark "),
        "ticks": ("tick", "grid"),
        "regression": ("regression", "line fitting"),
    }
    for topic, needles in rules.items():
        if any(needle in probe for needle in needles):
            topics.add(topic)
    return sorted(topics)


def _events(text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for match in EVENT_RE.finditer(text):
        if common._is_commented(text, match.start()):
            continue
        kind = match.group(1)
        open_index = match.end() - 1
        try:
            value, end = common._read_balanced_braces(text, open_index)
        except ValueError:
            continue
        result.append(
            {
                "kind": kind,
                "value": value.strip(),
                "start": match.start(),
                "end": end,
                "line": text.count("\n", 0, match.start()) + 1,
            }
        )
    return result


def _resolve_include(source_root: Path, value: str) -> Path | None:
    candidate = value.strip()
    if not candidate or "\\" in candidate or "#" in candidate:
        return None
    path = source_root / candidate
    if not candidate.endswith(".tex"):
        path = source_root / f"{candidate}.tex"
    return path if path.is_file() else None


def _walk_file(
    path: Path,
    source_root: Path,
    manifest: dict[str, Any],
    inherited: list[tuple[int, str]],
    seen: set[Path],
) -> list[dict[str, Any]]:
    if path in seen:
        return []
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    events = _events(text)
    headings = [event for event in events if event["kind"] in HEADING_LEVELS]
    entries: list[dict[str, Any]] = []
    stack = list(inherited)

    for index, event in enumerate(events):
        kind = event["kind"]
        if kind in HEADING_LEVELS:
            level = HEADING_LEVELS[kind]
            title = _plain_title(event["value"]) or event["value"]
            stack = [item for item in stack if item[0] < level]
            stack.append((level, title))
            next_heading = next(
                (
                    item
                    for item in events[index + 1 :]
                    if item["kind"] in HEADING_LEVELS
                ),
                None,
            )
            body_end = next_heading["start"] if next_heading else len(text)
            raw = text[event["end"] : body_end]
            body = _plain_body(raw)
            if not body and level == 1:
                body = title
            source_file = path.relative_to(source_root).as_posix()
            line_end = text.count("\n", 0, body_end) + 1
            libraries = _libraries(raw, path.name)
            commands = sorted(set(COMMAND_RE.findall(raw)))
            keys = _declared_keys(raw)
            topic_ids = _topic_ids(title, source_file, libraries)
            entries.append(
                {
                    "id": (
                        "pgfplots-manual-"
                        + re.sub(r"[^a-z0-9]+", "-", path.stem.casefold()).strip("-")
                        + f"-l{event['line']:04d}"
                    ),
                    "source_id": manifest["source_id"],
                    "source_version": manifest["version"],
                    "source_file": f"doc/latex/pgfplots/{source_file}",
                    "line_start": event["line"],
                    "line_end": max(event["line"], line_end),
                    "section": title,
                    "section_level": level,
                    "section_path": [value for _, value in stack],
                    "title": title,
                    "aliases": [],
                    "topic_ids": topic_ids,
                    "commands": commands,
                    "keys": keys,
                    "libraries": libraries,
                    "contains_code_example": r"\begin{codeexample}" in raw,
                    "text": body,
                }
            )
        else:
            include_path = _resolve_include(source_root, event["value"])
            if include_path is not None:
                entries.extend(
                    _walk_file(
                        include_path,
                        source_root,
                        manifest,
                        stack,
                        seen,
                    )
                )
    return entries


def _build_entries() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _load_json(SOURCE_MANIFEST)
    source_root = ROOT / manifest["source_root"]
    actual_hash = pgfplots_examples._canonical_tree_sha256(source_root)
    if actual_hash != manifest["tree_sha256"]:
        raise RuntimeError(
            "PGFPlots source tree hash mismatch: "
            f"expected {manifest['tree_sha256']}, got {actual_hash}"
        )
    root_file = source_root / "pgfplots.tex"
    entries = _walk_file(root_file, source_root, manifest, [], set())
    ids = [item["id"] for item in entries]
    if len(ids) != len(set(ids)):
        duplicates = [key for key, count in Counter(ids).items() if count > 1]
        raise RuntimeError(f"duplicate PGFPlots manual IDs: {duplicates}")
    return manifest, entries


def _topics_payload(manifest: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    libraries: dict[str, list[str]] = {}
    topics: dict[str, list[str]] = {}
    for item in entries:
        for library in item["libraries"]:
            libraries.setdefault(library, []).append(item["id"])
        for topic in item["topic_ids"]:
            topics.setdefault(topic, []).append(item["id"])
    return {
        "schema_version": "1.0",
        "source_id": manifest["source_id"],
        "source_version": manifest["version"],
        "total_chunks": len(entries),
        "source_files": len({item["source_file"] for item in entries}),
        "chapters": [
            {"id": item["id"], "title": item["title"]}
            for item in entries
            if item["section_level"] == 1
        ],
        "libraries": [
            {"library": name, "chunk_ids": ids}
            for name, ids in sorted(libraries.items())
        ],
        "topics": [
            {"topic": name, "chunk_ids": ids}
            for name, ids in sorted(topics.items())
        ],
    }


def build(write: bool = True) -> tuple[dict[str, Any], list[dict[str, Any]], str, str]:
    manifest, entries = _build_entries()
    jsonl = "".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
        for item in entries
    )
    topics_json = json.dumps(
        _topics_payload(manifest, entries),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(jsonl, encoding="utf-8")
        TOPICS.write_text(topics_json, encoding="utf-8")
    return manifest, entries, jsonl, topics_json


def verify() -> None:
    manifest, entries, jsonl, topics_json = build(write=False)
    expected = {OUTPUT: jsonl, TOPICS: topics_json}
    for path, content in expected.items():
        if not path.is_file():
            raise RuntimeError(f"missing generated PGFPlots manual corpus file: {path}")
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"generated PGFPlots manual corpus is stale: {path}")
    if not any(item["title"] == "Error Bars" for item in entries):
        raise RuntimeError("PGFPlots manual corpus is missing Error Bars")
    if not any("groupplots" in item["topic_ids"] for item in entries):
        raise RuntimeError("PGFPlots manual corpus is missing groupplots topic")
    print(
        "ok: pgfplots manual corpus "
        f"chunks={len(entries)} files={len({item['source_file'] for item in entries})} "
        f"version={manifest['version']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "verify"))
    args = parser.parse_args(argv)
    if args.action == "build":
        manifest, entries, _, _ = build(write=True)
        print(
            f"ok: wrote {len(entries)} PGFPlots {manifest['version']} manual chunks "
            f"to {OUTPUT.relative_to(ROOT)}"
        )
    else:
        verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
