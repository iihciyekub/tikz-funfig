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
                "summary": (item.get("text") or "")[:360].replace("\n", " "),
                "body": item.get("text", ""),
                "source": item.get("source_id", ""),
                "status": "official-source",
                "pages": f"{item.get('page_start')}-{item.get('page_end')}",
            }


def all_entries(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or knowledge_root()
    return [*_card_entries(root), *_manual_entries(root)]


def _join(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")


def _fts_connection(entries: list[dict[str, Any]]) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE VIRTUAL TABLE knowledge USING fts5("
        "id UNINDEXED, kind UNINDEXED, status UNINDEXED, pages UNINDEXED, "
        "title, aliases, tags, commands, libraries, summary, body, source, "
        "tokenize='unicode61 remove_diacritics 2')"
    )
    connection.executemany(
        "INSERT INTO knowledge VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                item["id"], item["kind"], item["status"], item["pages"],
                item["title"], _join(item["aliases"]), _join(item["tags"]),
                _join(item["commands"]), _join(item["libraries"]),
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
        rows = connection.execute(
            "SELECT id,kind,title,status,pages,bm25(knowledge,0,0,0,0,7,5,4,5,5,3,1,1) AS score,summary,source "
            "FROM knowledge WHERE knowledge MATCH ? ORDER BY score LIMIT ?",
            (_fts_query(normalized), int(limit)),
        ).fetchall()
    finally:
        connection.close()
    return [KnowledgeHit(*row) for row in rows]


def status(root: Path | None = None) -> dict[str, Any]:
    root = root or knowledge_root()
    entries = all_entries(root)
    return {
        "root": str(root),
        "cards": sum(item["kind"] == "card" for item in entries),
        "manual_chunks": sum(item["kind"] == "manual" for item in entries),
        "verification": {
            state: sum(item["status"] == state for item in entries if item["kind"] == "card")
            for state in ("draft", "reviewed", "compiled")
        },
    }
