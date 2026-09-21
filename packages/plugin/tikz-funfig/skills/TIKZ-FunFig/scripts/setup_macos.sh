#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "error: setup_macos.sh is intended for macOS" >&2
  exit 69
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "error: Homebrew is required for automatic dependency installation" >&2
  echo "install Homebrew first, then run this script again" >&2
  exit 69
fi

if command -v gnuplot >/dev/null 2>&1; then
  echo "ok: $(gnuplot --version)"
else
  echo "installing gnuplot with Homebrew..."
  brew install gnuplot
fi

if command -v pdftocairo >/dev/null 2>&1; then
  echo "ok: $(pdftocairo -v 2>&1 | head -n 1)"
else
  echo "installing poppler for SVG export with Homebrew..."
  brew install poppler
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
"$script_dir/check_dependencies.sh"
