#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
workspace_root="$(cd "$script_dir/../../../.." && pwd)"
repo_root="$workspace_root/tikz-funfig"

if [[ ! -f "$repo_root/pyproject.toml" || ! -d "$repo_root/src/funfig" ]]; then
  echo "error: TIKZ-FunFig source project was not found at: $repo_root" >&2
  exit 66
fi

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m funfig "$@"

