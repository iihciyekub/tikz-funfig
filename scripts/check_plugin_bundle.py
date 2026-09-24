#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "packages/plugin/tikz-funfig"
MAX_BYTES = 25 * 1024 * 1024

FORBIDDEN_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".funfig",
}

FORBIDDEN_SUFFIXES = {
    ".pdf",
    ".aux",
    ".log",
    ".fls",
    ".fdb_latexmk",
    ".synctex.gz",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
}


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def main() -> int:
    if not PLUGIN.is_dir():
        fail(f"portable Plugin does not exist: {PLUGIN}")

    files = sorted(path for path in PLUGIN.rglob("*") if path.is_file())
    total = sum(path.stat().st_size for path in files)
    if total > MAX_BYTES:
        fail(
            f"portable Plugin is {total / 1024 / 1024:.2f} MiB; "
            f"budget is {MAX_BYTES / 1024 / 1024:.0f} MiB"
        )

    forbidden: list[str] = []
    for path in files:
        relative = path.relative_to(PLUGIN)
        if any(part in FORBIDDEN_DIR_NAMES for part in relative.parts):
            forbidden.append(relative.as_posix())
            continue
        if path.name == ".DS_Store":
            forbidden.append(relative.as_posix())
            continue
        suffix = "".join(path.suffixes[-2:]) if path.name.endswith(".synctex.gz") else path.suffix
        if suffix.casefold() in FORBIDDEN_SUFFIXES:
            forbidden.append(relative.as_posix())

    for forbidden_root in (
        PLUGIN / "sources",
        PLUGIN / "references/legacy",
        PLUGIN / "references/manuals",
    ):
        if forbidden_root.exists():
            forbidden.append(forbidden_root.relative_to(PLUGIN).as_posix() + "/")

    if forbidden:
        fail("forbidden raw/build artifacts in Plugin: " + ", ".join(forbidden[:20]))

    required = (
        "plugin.json",
        "knowledge/cards/index.json",
        "knowledge/corpus/examples.jsonl",
        "knowledge/corpus/pgfplots-1.18.2.jsonl",
        "knowledge/corpus/community.jsonl",
        "runtime/templates/index.json",
        "runtime/schemas/figure-spec.schema.json",
        "skills/TIKZ-FunFig/SKILL.md",
        "skills/funfig-plots/SKILL.md",
        "skills/funfig-flowcharts/SKILL.md",
        "skills/funfig-frameworks/SKILL.md",
        "skills/funfig-relations/SKILL.md",
        "skills/funfig-schematics/SKILL.md",
    )
    missing = [name for name in required if not (PLUGIN / name).is_file()]
    if missing:
        fail("portable Plugin is missing required files: " + ", ".join(missing))

    manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "tikz-funfig":
        fail("portable Plugin manifest identity is not tikz-funfig")

    print(
        "ok: portable plugin "
        f"files={len(files)} size_mib={total / 1024 / 1024:.2f} "
        f"budget_mib={MAX_BYTES / 1024 / 1024:.0f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
