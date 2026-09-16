#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
export TFF_REPO_ROOT="$repo_root"

python3 <<'PY'
from __future__ import annotations

import os
import shutil
from pathlib import Path

root = Path(os.environ["TFF_REPO_ROOT"]).resolve()
removed: list[Path] = []


def remove_file(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.unlink()
        removed.append(path)


def remove_dir(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        removed.append(path)


for path in root.rglob(".DS_Store"):
    remove_file(path)

for path in root.rglob("__pycache__"):
    remove_dir(path)
remove_dir(root / ".pytest_cache")
remove_dir(root / ".smoke")

examples = root / "examples"
if examples.exists():
    for path in examples.rglob(".funfig"):
        remove_dir(path)
    for pattern in (
        "*.pdf",
        "*.aux",
        "*.fdb_latexmk",
        "*.fls",
        "*.log",
        "*.pgf-plot.gnuplot",
        "*.pgf-plot.table",
        "*_contourtmp*.dat",
        "*_contourtmp*.script",
    ):
        for path in examples.rglob(pattern):
            remove_file(path)
    for path in examples.rglob("figure.tex"):
        remove_file(path)

icon_root = root / "IconKitchen"
for dirname in ("android", "ios", "web"):
    remove_dir(icon_root / dirname)
macos = icon_root / "macos"
if macos.exists():
    keep = {"AppIcon128.png", "AppIcon512.png"}
    for path in macos.iterdir():
        if path.name not in keep:
            if path.is_dir():
                remove_dir(path)
            else:
                remove_file(path)

if removed:
    print(f"cleaned {len(removed)} generated/noise paths")
    for path in removed:
        try:
            print("  -", path.relative_to(root))
        except ValueError:
            print("  -", path)
else:
    print("clean: no generated/noise paths found")
PY

cd "$repo_root"
git status --short
