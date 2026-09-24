---
name: funfig-plots
description: Create and revise publication-quality mathematical, data, statistical, and scientific plots with TIKZ-FunFig and PGFPlots. Use for functions, measured data, error bars, confidence bands, scatter plots, threshold/regime figures, intersections, heatmaps, contours, surfaces, vector fields, and multi-panel plots. Do not use for concept networks or process diagrams whose primary structure is nodes and relationships rather than axes/data.
---

# FunFig Plots

Use the shared TIKZ-FunFig runtime. The packaged Skill materializes `scripts/funfig.sh`; use it for `capabilities`, `kb`, `validate`, `build`, and `inspect`. Keep `figure.funfig.json` as the canonical source for stable plot recipes.
Obey the shared TIKZ-FunFig output contract in `TIKZ-FunFig/references/output-policy.md`; do not choose a Plugin/Skill cache as an output directory.

## Workflow

1. Preserve existing FigureSpec/data when revising a managed figure.
2. Run `scripts/funfig.sh capabilities` and choose the nearest stable PGFPlots Recipe before inventing syntax. For common publication layouts, search/inspect curated Templates before composing a new layout.
3. Inspect the user's function/data semantics, axis bounds, units, uncertainty, annotations, and target journal size. Never invent scientific values.
4. Query `scripts/funfig.sh kb search "<need>"` when syntax or implementation details are uncertain. Prefer a compatible Recipe/Template, then compiled PGFPlots knowledge cards, then source-compiled official examples; use the normalized official PGFPlots manual for exact key semantics and long-tail reference details.
5. Create/update the FigureSpec, validate, render, and build.
6. Run `funfig inspect`; review the preview at the target publication size. Repair layout/labels before declaring completion.

Use `publication-threshold` for the mature threshold/regime/callout pattern, `groupplot` for structured panels, and the dedicated error/scatter/band/3D recipes before raw PGFPlots.

Expert TikZ/PGF mode is allowed only for a real long-tail requirement outside stable Recipes. Record official/card sources and compile with `expert-build`; do not treat one raw solution as a new stable capability.
