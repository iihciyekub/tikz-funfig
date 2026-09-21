#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
bin_dir="${TFF_BIN_DIR:-$HOME/.local/bin}"
cli_only=0
if [ "${1:-}" = "--cli-only" ]; then
  cli_only=1
  shift
fi
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  echo "Usage: $0 [--cli-only] [--skip-doctor]"
  echo "Install the tff helper, then install/update the Git-backed Codex plugin."
  exit 0
fi
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--skip-doctor" ]; }; then
  echo "error: expected --cli-only and/or --skip-doctor" >&2
  exit 2
fi
command -v python3 >/dev/null 2>&1 || { echo "error: python3 is required" >&2; exit 1; }

mkdir -p "$bin_dir"
helper_tmp="$(mktemp "$bin_dir/.tff-XXXXXX")"
trap 'rm -f "$helper_tmp"' EXIT
cp "$repo_root/scripts/tff" "$helper_tmp"
chmod +x "$helper_tmp"
mv -f "$helper_tmp" "$bin_dir/tff"
echo "ok: installed helper -> $bin_dir/tff"
"$bin_dir/tff" --version

case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *)
    echo "note: add $bin_dir to PATH, or use the absolute helper path above" >&2
    ;;
esac

if [ "$cli_only" -eq 0 ]; then
  "$bin_dir/tff" install "$@"
fi
echo "install: tff install | update: tff update | status: tff status"
