#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
plugin_root="$repo_root/packages/plugin/tikz-funfig"

mkdir -p "$plugin_root/assets" "$plugin_root/skills" "$plugin_root/runtime/src"

python3 - "$repo_root" "$plugin_root" <<'PY'
from pathlib import Path
import shutil
import sys

repo = Path(sys.argv[1])
plugin = Path(sys.argv[2])

def refresh(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)

refresh(repo / "packages/skill", plugin / "skills/TIKZ-FunFig")
refresh(repo / "src/funfig", plugin / "runtime/src/funfig")
refresh(repo / "schemas", plugin / "runtime/schemas")
refresh(repo / "recipes", plugin / "runtime/recipes")
PY

cp "$repo_root/IconKitchen/macos/AppIcon128.png" "$plugin_root/assets/icon.png"
cp "$repo_root/IconKitchen/macos/AppIcon512.png" "$plugin_root/assets/logo.png"

echo "ok: synchronized portable plugin -> $plugin_root"
