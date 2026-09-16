#!/usr/bin/env bash
set -euo pipefail

required=(latexmk pdflatex xelatex gnuplot)
missing=0

echo "TIKZ-FunFig dependency check"
echo

for cmd in "${required[@]}"; do
  if path="$(command -v "$cmd" 2>/dev/null)"; then
    version=""
    case "$cmd" in
      gnuplot)
        version="$(gnuplot --version 2>/dev/null || true)"
        ;;
      latexmk)
        version="$(latexmk -v 2>/dev/null | head -n 1 || true)"
        ;;
      pdflatex|xelatex)
        version="$($cmd --version 2>/dev/null | head -n 1 || true)"
        ;;
    esac
    printf 'ok      %-10s %s\n' "$cmd" "$path"
    [[ -n "$version" ]] && printf '        %s\n' "$version"
  else
    printf 'missing %-10s\n' "$cmd"
    missing=1
  fi
done

echo
if [[ "$missing" -eq 0 ]]; then
  echo "ok: full TIKZ-FunFig toolchain is available"
else
  echo "error: one or more TIKZ-FunFig dependencies are missing" >&2
  if ! command -v gnuplot >/dev/null 2>&1; then
    echo "hint: on macOS install gnuplot with: brew install gnuplot" >&2
  fi
  exit 69
fi

