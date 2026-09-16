#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

if command -v tff >/dev/null 2>&1; then
  exec tff update
fi

exec "$repo_root/scripts/tff" update
