from __future__ import annotations

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "figure-spec.schema.json"
RECIPES_DIR = PROJECT_ROOT / "recipes"
RECIPE_INDEX_PATH = RECIPES_DIR / "index.json"


def project_root() -> Path:
    return PROJECT_ROOT

