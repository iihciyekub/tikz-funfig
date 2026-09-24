# PGFPlots official source

This directory pins the official PGFPlots documentation source used to build
TIKZ-FunFig's plot source-example corpus.

- Upstream project: <https://github.com/pgf-tikz/pgfplots>
- Pinned release: `1.18.2`
- Pinned commit: `d8d5424dafa7424df3fbf77022b8f662fffaa4fb`
- Raw documentation source: `upstream/doc/latex/pgfplots/`
- Snapshot hash covers canonical vendored documentation files and deliberately
  excludes Finder metadata and upstream-ignored generated PNG/PDF/gnuplot
  artifacts, so local preview/build noise cannot invalidate the pin.
- Upstream license notice: `upstream/README.md`
- Runtime corpus: `../../../knowledge/corpus/pgfplots-1.18.2.jsonl`

The raw upstream tree is development/provenance input and is never copied into
the portable Plugin. Only normalized source-example metadata/code is eligible
for runtime distribution.
