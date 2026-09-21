from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _root(name: str) -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / name
        if (candidate / "index.json").is_file():
            return candidate
    raise ValueError(f"TIKZ-FunFig {name} root could not be located")


def _load(root: Path, item_id: str) -> dict[str, Any]:
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    record = next((item for item in index.get("items", []) if item.get("id") == item_id), None)
    if not record:
        raise ValueError(f"unknown {root.name[:-1] if root.name.endswith('s') else root.name}: {item_id!r}")
    payload = json.loads((root / record["file"]).read_text(encoding="utf-8"))
    if payload.get("id") != item_id:
        raise ValueError(f"{root.name} index mismatch for {item_id!r}")
    return payload


def load_theme(theme_id: str) -> dict[str, Any]:
    return _load(_root("themes"), theme_id)


def load_profile(profile_id: str) -> dict[str, Any]:
    return _load(_root("profiles"), profile_id)


def list_themes() -> list[dict[str, Any]]:
    root = _root("themes")
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    return [_load(root, item["id"]) for item in index.get("items", [])]


def list_profiles() -> list[dict[str, Any]]:
    root = _root("profiles")
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    return [_load(root, item["id"]) for item in index.get("items", [])]
