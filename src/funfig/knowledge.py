from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class KnowledgeHit:
    id: str
    kind: str
    title: str
    status: str
    pages: str
    score: float
    summary: str
    source: str


def knowledge_root() -> Path:
    override = os.environ.get("TFF_KNOWLEDGE_ROOT")
    if override:
        root = Path(override).expanduser().resolve()
        if root.is_dir():
            return root
        raise ValueError(f"TFF_KNOWLEDGE_ROOT does not exist: {root}")

    here = Path(__file__).resolve()
    candidates = []
    for parent in here.parents:
        candidates.append(parent / "knowledge")
    for candidate in candidates:
        if (candidate / "cards/index.json").is_file():
            return candidate
    raise ValueError("TIKZ-FunFig knowledge root could not be located")


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _aliases(root: Path) -> dict[str, str]:
    path = root / "aliases.json"
    return _json(path) if path.is_file() else {}


def normalize_query(query: str, root: Path | None = None) -> str:
    root = root or knowledge_root()
    result = query.strip()
    lowered = result.casefold()
    for source, target in _aliases(root).items():
        if source.casefold() in lowered:
            result += " " + target
    return re.sub(r"\s+", " ", result).strip()


def _card_entries(root: Path) -> Iterable[dict[str, Any]]:
    index = _json(root / "cards/index.json")
    for item in index.get("cards", []):
        path = root / "cards" / item["file"]
        body = path.read_text(encoding="utf-8") if path.is_file() else ""
        yield {
            "id": item["id"],
            "kind": "card",
            "title": item["title"],
            "aliases": item.get("aliases", []),
            "tags": item.get("tags", []),
            "commands": item.get("commands", []),
            "libraries": item.get("libraries", []),
            "families": item.get("tags", []),
            "layout": [],
            "style": [],
            "summary": item.get("summary", ""),
            "body": body,
            "source": ", ".join(item.get("sources", [])),
            "status": item.get("verification", "draft"),
            "pages": ", ".join(str(value) for value in item.get("pages", [])),
        }


def _manual_entries(root: Path) -> Iterable[dict[str, Any]]:
    directory = root / "manual-index"
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            yield {
                "id": item["id"],
                "kind": "manual",
                "title": item.get("title") or item["id"],
                "aliases": item.get("aliases", []),
                "tags": item.get("topic_ids", []),
                "commands": item.get("commands", []),
                "libraries": item.get("libraries", []),
                "families": item.get("topic_ids", []),
                "layout": [],
                "style": [],
                "summary": (item.get("text") or "")[:360].replace("\n", " "),
                "body": item.get("text", ""),
                "source": item.get("source_id", ""),
                "status": "official-source",
                "pages": f"{item.get('page_start')}-{item.get('page_end')}",
            }


def _corpus_entries(root: Path) -> Iterable[dict[str, Any]]:
    path = root / "corpus/examples.jsonl"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        locator = item.get("source_locator", {})
        source_path = locator.get("path", "")
        line_start = locator.get("line_start")
        line_end = locator.get("line_end")
        location = ""
        if line_start:
            location = f"L{line_start}" + (f"-L{line_end}" if line_end and line_end != line_start else "")
        source = source_path + (f":{location}" if location else "")
        aliases = [
            *item.get("tags", []),
            *item.get("figure_families", []),
            *item.get("layout_traits", []),
            *item.get("style_traits", []),
        ]
        yield {
            "id": item["id"],
            "kind": "example",
            "title": item.get("title") or item["id"],
            "aliases": aliases,
            "tags": item.get("tags", []),
            "commands": item.get("commands", []),
            "libraries": item.get("libraries", []),
            "families": item.get("figure_families", []),
            "layout": item.get("layout_traits", []),
            "style": item.get("style_traits", []),
            "summary": item.get("summary", ""),
            "body": item.get("code", ""),
            "source": source,
            "status": item.get("verification", "source-extracted"),
            "pages": location,
        }


def _recipe_root(root: Path) -> Path | None:
    candidates = (
        root.parent / "recipes",
        root.parent / "runtime/recipes",
    )
    for candidate in candidates:
        if (candidate / "index.json").is_file():
            return candidate
    return None


def _recipe_entries(root: Path) -> Iterable[dict[str, Any]]:
    directory = _recipe_root(root)
    if directory is None:
        return
    index = _json(directory / "index.json")
    for recipe_id in index.get("recipes", []):
        path = directory / f"{recipe_id}.recipe.json"
        if not path.is_file():
            continue
        item = _json(path)
        capabilities = item.get("capabilities", [])
        roles = item.get("roles", [])
        aliases = [*capabilities, *roles, *item.get("knowledge_ids", [])]
        yield {
            "id": item["id"],
            "kind": "recipe",
            "title": item.get("description") or item["id"],
            "aliases": aliases,
            "tags": [item.get("kind", ""), *capabilities],
            "commands": [],
            "libraries": [],
            "families": [item["id"], item.get("kind", "")],
            "layout": capabilities,
            "style": [],
            "summary": item.get("description", ""),
            "body": json.dumps(item, ensure_ascii=False, sort_keys=True),
            "source": f"recipes/{path.name}",
            "status": item.get("status", "experimental"),
            "pages": "",
        }


def _template_entries(root: Path) -> Iterable[dict[str, Any]]:
    candidates = (
        root.parent / "examples/templates",
        root.parent / "runtime/templates",
    )
    directory = next(
        (candidate for candidate in candidates if (candidate / "index.json").is_file()),
        None,
    )
    if directory is None:
        return
    index = _json(directory / "index.json")
    for item in index.get("templates", []):
        path = directory / item["path"] / "template.meta.json"
        if not path.is_file():
            continue
        meta = _json(path)
        contract = meta.get("edit_contract", {})
        yield {
            "id": meta["id"],
            "kind": "template",
            "title": meta.get("title") or meta["id"],
            "aliases": [
                *meta.get("tags", []),
                meta.get("family", ""),
                meta.get("recipe_hint", ""),
            ],
            "tags": meta.get("tags", []),
            "commands": [],
            "libraries": meta.get("requires", {}).get("libraries", []),
            "families": [meta.get("family", ""), meta.get("recipe_hint", "")],
            "layout": list(contract.get("structural_limits", {}).keys()),
            "style": [
                *meta.get("supported_profiles", []),
                *meta.get("supported_themes", []),
            ],
            "summary": meta.get("description", ""),
            "body": json.dumps(meta, ensure_ascii=False, sort_keys=True),
            "source": f"templates/{item['path']}/template.meta.json",
            "status": meta.get("verification", "draft"),
            "pages": "",
        }


def all_entries(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or knowledge_root()
    return [
        *_recipe_entries(root),
        *_template_entries(root),
        *_card_entries(root),
        *_corpus_entries(root),
        *_manual_entries(root),
    ]


def _join(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")


def _fts_connection(entries: list[dict[str, Any]]) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE VIRTUAL TABLE knowledge USING fts5("
        "id UNINDEXED, kind UNINDEXED, status UNINDEXED, pages UNINDEXED, "
        "title, aliases, tags, commands, libraries, families, layout, style, "
        "summary, body, source, "
        "tokenize='unicode61 remove_diacritics 2')"
    )
    connection.executemany(
        "INSERT INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                item["id"], item["kind"], item["status"], item["pages"],
                item["title"], _join(item["aliases"]), _join(item["tags"]),
                _join(item["commands"]), _join(item["libraries"]),
                _join(item["families"]), _join(item["layout"]), _join(item["style"]),
                item["summary"], item["body"], item["source"],
            )
            for item in entries
        ],
    )
    return connection


def _fts_query(query: str) -> str:
    # FTS5 treats punctuation in raw TikZ commands as syntax. Quote each token
    # so user input such as \draw, arrows.meta, or Chinese phrases remains safe.
    tokens = [token for token in re.split(r"\s+", query) if token]
    if not tokens:
        return '""'
    escaped = [token.replace('"', '""') for token in tokens]
    return " OR ".join(f'"{token}"' for token in escaped)


def search(query: str, limit: int = 8, root: Path | None = None) -> list[KnowledgeHit]:
    root = root or knowledge_root()
    normalized = normalize_query(query, root)
    entries = all_entries(root)
    if not entries:
        return []
    connection = _fts_connection(entries)
    try:
        candidate_limit = max(int(limit) * 10, int(limit))
        rows = connection.execute(
            "SELECT id,kind,title,status,pages,"
            "bm25(knowledge,0,0,0,0,8,7,6,9,9,10,8,5,4,1,1) * "
            "CASE "
            "WHEN kind='card' AND status='compiled' THEN 1.30 "
            "WHEN kind='template' AND status='compiled-and-regression-backed' THEN 1.16 "
            "WHEN kind='template' THEN 1.05 "
            "WHEN kind='recipe' AND status='stable' THEN 1.20 "
            "WHEN kind='recipe' THEN 1.10 "
            "WHEN kind='example' AND status='source-compiled' THEN 1.08 "
            "WHEN kind='example' THEN 1.00 "
            "WHEN kind='manual' THEN 0.92 "
            "ELSE 1.00 END AS score,summary,source "
            "FROM knowledge WHERE knowledge MATCH ? ORDER BY score LIMIT ?",
            (_fts_query(normalized), candidate_limit),
        ).fetchall()
    finally:
        connection.close()
    hits: list[KnowledgeHit] = []
    example_sources: dict[str, int] = {}
    for row in rows:
        hit = KnowledgeHit(*row)
        if hit.kind == "example":
            source_group = hit.source.split(":L", 1)[0]
            seen = example_sources.get(source_group, 0)
            if seen >= 2:
                continue
            example_sources[source_group] = seen + 1
        hits.append(hit)
        if len(hits) >= int(limit):
            break
    return hits


def status(root: Path | None = None) -> dict[str, Any]:
    root = root or knowledge_root()
    entries = all_entries(root)
    return {
        "root": str(root),
        "cards": sum(item["kind"] == "card" for item in entries),
        "manual_chunks": sum(item["kind"] == "manual" for item in entries),
        "source_examples": sum(item["kind"] == "example" for item in entries),
        "recipes": sum(item["kind"] == "recipe" for item in entries),
        "templates": sum(item["kind"] == "template" for item in entries),
        "kinds": {
            kind: sum(item["kind"] == kind for item in entries)
            for kind in ("recipe", "template", "card", "example", "manual")
        },
        "verification": {
            state: sum(item["status"] == state for item in entries if item["kind"] == "card")
            for state in ("draft", "reviewed", "compiled")
        },
        "example_verification": {
            state: sum(item["status"] == state for item in entries if item["kind"] == "example")
            for state in ("source-extracted", "source-compiled", "reviewed")
        },
    }
