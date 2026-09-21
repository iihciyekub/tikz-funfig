#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
plugin_root="$repo_root/packages/plugin/tikz-funfig"

mkdir -p "$plugin_root/assets" "$plugin_root/skills" "$plugin_root/runtime/src" "$plugin_root/scripts"

python3 - "$repo_root" "$plugin_root" <<'PY'
from pathlib import Path
import json
import re
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

version_source = (repo / "src/funfig/__init__.py").read_text(encoding="utf-8")
match = re.search(r'__version__\s*=\s*"([^"]+)"', version_source)
if not match:
    raise SystemExit("error: could not resolve funfig __version__")
manifest_path = plugin / "plugin.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = match.group(1)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

cp "$repo_root/IconKitchen/macos/AppIcon128.png" "$plugin_root/assets/icon.png"
cp "$repo_root/IconKitchen/macos/AppIcon512.png" "$plugin_root/assets/logo.png"
cp "$repo_root/scripts/tff" "$plugin_root/scripts/tff"
chmod +x "$plugin_root/scripts/tff"

echo "ok: synchronized portable plugin -> $plugin_root"
