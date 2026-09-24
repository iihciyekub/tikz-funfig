#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

version="${1:-}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "usage: $0 X.Y.Z" >&2
  exit 2
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "error: release requires a clean working tree; commit development changes first" >&2
  exit 1
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "error: git remote 'origin' is not configured" >&2
  exit 1
fi
if git rev-parse "v$version" >/dev/null 2>&1; then
  echo "error: tag v$version already exists" >&2
  exit 1
fi
if ! grep -Eq "^## \\[$version\\]( |$)" CHANGELOG.md; then
  echo "error: CHANGELOG.md must contain a release section for [$version] before release" >&2
  exit 1
fi

python3 scripts/version.py set "$version"
./scripts/sync_plugin_package.sh
python3 scripts/version.py check
./scripts/check.sh
git diff --check

git add CHANGELOG.md pyproject.toml src/funfig/__init__.py scripts/tff packages/plugin/tikz-funfig
# Version files may already have been prepared and committed during development.
# Still create the release marker commit before the immutable annotated tag.
git commit --allow-empty -m "release: v$version"
git tag -a "v$version" -m "TIKZ-FunFig v$version"
git push origin main
git push origin "v$version"

if command -v codex >/dev/null 2>&1 && [ "${TFF_SKIP_CODEX_UPDATE:-0}" != "1" ]; then
  ./scripts/update_codex.sh
fi

echo "ok: released TIKZ-FunFig v$version"
