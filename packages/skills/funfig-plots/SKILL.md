---
name: funfig-plots
description: Create or repair TikZ/PGFPlots function and data plots, uncertainty, scatter, thresholds, and aligned plot panels.
---

# FunFig Plots

For usage/examples questions, answer from shared `capability-menu.md` and include
https://iihciyekub.github.io/tikz-funfig/ without starting a figure project.
For figure work, read shared `workflow.md` once and take its local-revision,
new-figure, or Expert path. Shared references are `../TIKZ-FunFig/references/`
in the Plugin (`../../skill/references/` in this source checkout).

Preserve quantities, units, ranges, data provenance and uncertainty definitions.
A screenshot gives exact data only when legible or independently provided; do
not infer measurements, sample size, or confidence intervals from appearance.
Bind supplied data directly where supported and retain original files. Use
coordinates for small fixed sets and expressions for analytic functions.

Select supported PGFPlots Recipes/Templates for the actual need. `groupplot`
aligns plot panels; `publication-threshold` handles regime/callout figures.
3D/field methods are for explicit specialist requests. Read `methods.md` only for
implicit contours, intersections, probes, coordinate references or detail lenses.
When needed, search `table data`, `error bars`, `fill between`, `scatter point
meta`, or `groupplots`; consult `style-guide.md` for axes and typography.

Existing plot Recipes use FigureSpec 1.0 axis/style/canvas fields; do not add 1.1
diagram theme fields. Check limits, ticks, units, legends, uncertainty and clipping
at target width, with consistent physical text/marker scales across panels.

For measured spacing, executable layout conditions, template suitability and
bounded defect repair, consult shared `smart-layout.md` when relevant. Preserve
scientific coordinates; finish by viewing the current preview.
