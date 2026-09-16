#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 path/to/figure.tex" >&2
  exit 64
fi

src="$1"
if [[ ! -f "$src" ]]; then
  echo "error: file not found: $src" >&2
  exit 66
fi

src_dir="$(cd "$(dirname "$src")" && pwd)"
src_name="$(basename "$src")"

cd "$src_dir"

engine="pdflatex"
if grep -Eq '(^|[^A-Za-z])(xeCJK|fontspec)|TEX[[:space:]]+program[[:space:]]*=[[:space:]]*xelatex' "$src_name"; then
  engine="xelatex"
fi

needs_gnuplot=0
if grep -Eq 'raw[[:space:]]+gnuplot|\\addplot\+?[[:space:]]+gnuplot|\\addplot3\+?[[:space:]]+gnuplot' "$src_name"; then
  needs_gnuplot=1
fi

if ! command -v latexmk >/dev/null 2>&1; then
  echo "error: latexmk is not available" >&2
  exit 69
fi

latexmk_extra=()
if [[ "$needs_gnuplot" -eq 1 ]]; then
  if ! command -v gnuplot >/dev/null 2>&1; then
    echo "error: this figure uses PGFPlots gnuplot/raw gnuplot, but gnuplot is not installed" >&2
    echo "hint: on macOS run: brew install gnuplot" >&2
    exit 69
  fi
  # PGFPlots must launch gnuplot externally. Use this only for trusted or
  # reviewed TeX source.
  latexmk_extra+=("-latexoption=-shell-escape")
  echo "info: gnuplot detected: $(gnuplot --version)"
  echo "info: enabling TeX shell escape for this trusted gnuplot-backed source"
fi

case "$engine" in
  xelatex)
    latexmk -xelatex "${latexmk_extra[@]}" -interaction=nonstopmode -halt-on-error -file-line-error "$src_name"
    ;;
  *)
    latexmk -pdf "${latexmk_extra[@]}" -interaction=nonstopmode -halt-on-error -file-line-error "$src_name"
    ;;
esac

pdf="${src_name%.tex}.pdf"
if [[ -f "$pdf" ]]; then
  echo "ok: $src_dir/$pdf"
fi
