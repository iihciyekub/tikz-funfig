# PGF/TikZ manual source record

This directory pins the local `references/pgfmanual.pdf` input used to build the
TIKZ-FunFig official-reference index. The PDF itself remains the authoritative
source and is never overwritten by the build pipeline.

- `source.json` verifies version, SHA-256, and page count.
- `split-plan.json` defines complete first-level booklets and focused excerpts.
- `topics.json` provides stable task aliases and cross-chapter source ranges.

Run `python3 scripts/build_manual_reference.py verify` before rebuilding derived
reference artifacts. Generated PDF booklets live under `output/` and stay out of
the portable plugin. The searchable section corpus is generated under
`knowledge/manual-index/`.
