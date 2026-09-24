# PGF/TikZ manual source record

This directory pins the optional local `references/pgfmanual.pdf` input used
to build the historical PDF-derived TIKZ-FunFig section index. The PDF is a
development/provenance source and is never overwritten by the build pipeline.

The preferred code/example source is the pinned PGF/TikZ LaTeX documentation
snapshot under `../../upstream/doc/generic/pgf/`.

- `source.json` verifies version, SHA-256, and page count.
- `split-plan.json` defines complete first-level booklets and focused excerpts.
- `topics.json` provides stable task aliases and cross-chapter source ranges.

Run `python3 scripts/build_manual_reference.py verify` before rebuilding derived
reference artifacts. Generated PDF booklets live under `output/` and stay out of
the portable plugin. The searchable section corpus is generated under
`knowledge/manual-index/`.
