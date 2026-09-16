#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
workspace_root="$(cd "$repo_root/.." && pwd)"
source_dir="$repo_root/packages/skill/"
target_dir="${1:-$workspace_root/.agents/skills/TIKZ-FunFig/}"

if [[ ! -f "${source_dir}SKILL.md" ]]; then
  echo "error: skill package is missing: ${source_dir}SKILL.md" >&2
  exit 66
fi

mkdir -p "$target_dir"
rsync -a --delete --exclude '.smoke/' "$source_dir" "$target_dir"
echo "ok: synchronized TIKZ-FunFig skill -> $target_dir"

