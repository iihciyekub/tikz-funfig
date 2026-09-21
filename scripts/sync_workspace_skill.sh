#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
workspace_root="$(cd "$repo_root/.." && pwd)"
source_dir="$repo_root/packages/skill/"
requested_target="${1:-$workspace_root/.agents/skills/}"

if [[ "$(basename "$requested_target")" == "TIKZ-FunFig" ]]; then
  skills_root="$(cd "$(dirname "$requested_target")" && pwd)"
else
  mkdir -p "$requested_target"
  skills_root="$(cd "$requested_target" && pwd)"
fi
target_dir="$skills_root/TIKZ-FunFig/"

if [[ ! -f "${source_dir}SKILL.md" ]]; then
  echo "error: skill package is missing: ${source_dir}SKILL.md" >&2
  exit 66
fi

mkdir -p "$target_dir"
rsync -a --delete --exclude '.smoke/' "$source_dir" "$target_dir"

python3 - "$repo_root" "$skills_root" <<'PY'
from pathlib import Path
import json
import shutil
import sys

repo = Path(sys.argv[1])
skills_root = Path(sys.argv[2])
manifest = json.loads((repo / "packages/skills/index.json").read_text(encoding="utf-8"))
wrapper = repo / "packages/skill/scripts/funfig.sh"

for item in manifest.get("skills", []):
    source = repo / item["source_dir"]
    destination = skills_root / item["skill_id"]
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    scripts = destination / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wrapper, scripts / "funfig.sh")
PY

echo "ok: synchronized TIKZ-FunFig skill set -> $skills_root"

