#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "$script_dir/../../.." && pwd)"

# Portable Plugin installs bundle the FunFig runtime beside skills/. Prefer
# that copy so a cached Codex Plugin does not depend on the source checkout.
if [[ -d "$plugin_root/runtime/src/funfig" && -d "$plugin_root/runtime/recipes" ]]; then
  export PYTHONPATH="$plugin_root/runtime/src${PYTHONPATH:+:$PYTHONPATH}"
  exec python3 -m funfig "$@"
fi

workspace_root="$(cd "$script_dir/../../../.." && pwd)"
repo_root="$workspace_root/tikz-funfig"

if [[ ! -f "$repo_root/pyproject.toml" || ! -d "$repo_root/src/funfig" ]]; then
  echo "error: TIKZ-FunFig source project was not found at: $repo_root" >&2
  exit 66
fi

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m funfig "$@"

