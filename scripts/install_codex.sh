#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
bin_dir="${TFF_BIN_DIR:-$HOME/.local/bin}"

mkdir -p "$bin_dir"
cp "$repo_root/scripts/tff" "$bin_dir/tff"
chmod +x "$bin_dir/tff"

case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *)
    echo "note: add $bin_dir to PATH to call 'tff' from any shell" >&2
    ;;
esac

"$bin_dir/tff" install
echo "ok: installed helper -> $bin_dir/tff"
echo "next updates: tff update"
