from __future__ import annotations

from typing import Any

from .io import load_json
from .paths import RECIPE_INDEX_PATH, RECIPES_DIR


def recipe_ids() -> list[str]:
    index = load_json(RECIPE_INDEX_PATH)
    values = index.get("recipes", [])
    if not isinstance(values, list):
        raise ValueError("recipes/index.json has an invalid recipes list")
    return [str(value) for value in values]


def load_recipe(recipe_id: str) -> dict[str, Any]:
    if recipe_id not in recipe_ids():
        raise KeyError(f"unknown recipe: {recipe_id}")
    path = RECIPES_DIR / f"{recipe_id}.recipe.json"
    recipe = load_json(path)
    if recipe.get("id") != recipe_id:
        raise ValueError(f"recipe id mismatch in {path}")
    return recipe


def list_recipes() -> list[dict[str, Any]]:
    return [load_recipe(recipe_id) for recipe_id in recipe_ids()]

