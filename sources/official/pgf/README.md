# PGF/TikZ official source

This directory pins the official PGF/TikZ documentation source used to build
TIKZ-FunFig's manual and source-example knowledge.

- Upstream project: <https://github.com/pgf-tikz/pgf>
- Pinned revision: `3.1.11a`
- Raw source: `upstream/doc/generic/pgf/`
- Existing PDF-derived manifests: `derived/pdf-index/`
- Runtime section corpus: `../../../knowledge/manual-index/`

The raw upstream tree is never copied into the portable Plugin. Importers may
read it during development and write normalized, auditable outputs under
`knowledge/`.

The upstream snapshot contains its own license files under
`upstream/doc/generic/pgf/licenses/`; preserve them unchanged.

