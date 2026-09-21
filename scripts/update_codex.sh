#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
# Use the current checkout's helper, not an older tff earlier on PATH.
"$repo_root/scripts/install_codex.sh" --cli-only
exec "${TFF_BIN_DIR:-$HOME/.local/bin}/tff" update "$@"
