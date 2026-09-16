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

python3 - "$version" <<'PY'
from pathlib import Path
import re
import sys

version = sys.argv[1]

init = Path("src/funfig/__init__.py")
text = init.read_text(encoding="utf-8")
text = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{version}"', text)
init.write_text(text, encoding="utf-8")

pyproject = Path("pyproject.toml")
text = pyproject.read_text(encoding="utf-8")
text = re.sub(r'(?m)^version\s*=\s*"[^"]+"$', f'version = "{version}"', text, count=1)
pyproject.write_text(text, encoding="utf-8")

readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
text = re.sub(r'Version\s+\d+\.\d+(?:\.\d+)?', f'Version {version}', text, count=1)
readme.write_text(text, encoding="utf-8")
PY

./scripts/sync_plugin_package.sh
./scripts/check.sh
git diff --check

git add README.md pyproject.toml src/funfig/__init__.py packages/plugin/tikz-funfig
git commit -m "release: v$version"
git tag -a "v$version" -m "TIKZ-FunFig v$version"
git push origin main
git push origin "v$version"

if command -v codex >/dev/null 2>&1 && [ "${TFF_SKIP_CODEX_UPDATE:-0}" != "1" ]; then
  ./scripts/update_codex.sh
fi

echo "ok: released TIKZ-FunFig v$version"
