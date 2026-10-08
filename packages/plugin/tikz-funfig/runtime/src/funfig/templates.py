from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .layout import profile_for


def assess_template(item: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Apply declared structural limits before lexical/aesthetic ranking."""
    nodes = (spec.get('diagram') or {}).get('nodes', [])
    fit = item.get('design_fit') or {}
    limits = (item.get('edit_contract') or {}).get('structural_limits') or {}
    reasons = []
    if item.get('recipe_hint') != spec.get('recipe'):
        reasons.append('recipe/family differs from requested figure')
    for field, value in (('nodes', len(nodes)), ('decisions', sum(n.get('role') == 'decision' for n in nodes))):
        bounds = limits.get(field) or (fit.get('node_range') if field == 'nodes' else None)
        if bounds and not bounds[0] <= value <= bounds[1]:
            reasons.append(f'{field}={value} outside declared range {bounds}')
    width = profile_for(spec)['target_width_mm'] if spec.get('schema_version') == '1.1' else None
    widths = fit.get('recommended_width_mm')
    if widths and width and not widths[0] <= width <= widths[1]:
        reasons.append(f'target width {width} mm outside recommended {widths}')
    longest = max((sum(1 if ord(c) > 0x2E7F else .55 for c in n.get('label', '')) for n in nodes), default=0)
    density = fit.get('label_density', '')
    if 'short' in density and longest > 45:
        reasons.append('long labels exceed the short/medium-label design; reflow required')
    return {'eligible': not reasons, 'reasons': reasons, 'node_count': len(nodes),
            'target_width_mm': width, 'longest_label_em': round(longest, 1),
            'basis': 'declared template limits; confirm adapted preview'}


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
    spec: dict[str, Any] | None = None,
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
        if spec:
            item['suitability'] = assess_template(item, spec)
            if item.get('recipe_hint') == spec.get('recipe'):
                score += 10
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
    scored.sort(key=lambda value: (not value[2].get('suitability', {}).get('eligible', True), -value[0], value[1]))
    return [item for _, _, item in scored[: int(limit)]]
