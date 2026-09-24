from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT


def template_root() -> Path:
    candidates = (
        PROJECT_ROOT / "examples/templates",
        PROJECT_ROOT / "templates",
    )
    for candidate in candidates:
        if (candidate / "index.json").is_file():
            return candidate
    raise ValueError("TIKZ-FunFig template root could not be located")


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def list_templates(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or template_root()
    index = _json(root / "index.json")
    result: list[dict[str, Any]] = []
    for item in index.get("templates", []):
        directory = root / item["path"]
        meta_path = directory / "template.meta.json"
        spec_path = directory / "template.funfig.json"
        tex_path = directory / "template.tex"
        if not (meta_path.is_file() and spec_path.is_file() and tex_path.is_file()):
            raise ValueError(f"incomplete template: {directory}")
        meta = _json(meta_path)
        meta["path"] = item["path"]
        meta["spec"] = str(spec_path)
        meta["tex"] = str(tex_path)
        result.append(meta)
    return result


def get_template(template_id: str, root: Path | None = None) -> dict[str, Any]:
    for item in list_templates(root):
        if item["id"] == template_id:
            return item
    raise ValueError(f"unknown template: {template_id}")


def search_templates(
    query: str,
    limit: int = 8,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    tokens = [token.casefold() for token in query.split() if token.strip()]
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for item in list_templates(root):
        fields = {
            "id": item.get("id", ""),
            "family": item.get("family", ""),
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "recipe": item.get("recipe_hint", ""),
            "tags": " ".join(item.get("tags", [])),
            "design_fit": json.dumps(item.get("design_fit", {}), ensure_ascii=False),
        }
        score = 0
        for token in tokens:
            if token in fields["id"].casefold():
                score += 8
            if token in fields["family"].casefold():
                score += 7
            if token in fields["recipe"].casefold():
                score += 7
            if token in fields["title"].casefold():
                score += 6
            if token in fields["tags"].casefold():
                score += 5
            if token in fields["design_fit"].casefold():
                score += 4
            if token in fields["description"].casefold():
                score += 2
        if score:
            scored.append((score, item["id"], item))
    scored.sort(key=lambda value: (-value[0], value[1]))
    return [item for _, _, item in scored[: int(limit)]]
