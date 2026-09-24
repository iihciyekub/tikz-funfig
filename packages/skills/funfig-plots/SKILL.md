---
name: funfig-plots
description: Create and refine academic TikZ/PGFPlots data and function plots from descriptions, data, or reference figures. Use for axes, uncertainty, scientific fields, and aligned plot panels.
---

# FunFig Plots

Use the current Skill's `scripts/funfig.sh` wrapper from the user's project.
Shared references live in `../TIKZ-FunFig/references/` in the installed Plugin
(`../../skill/references/` in this source checkout). Read `workflow.md` once;
use its design, output, knowledge-retrieval, and visual-review contracts.
For any supplied image, also read `reference-images.md`; distinguish content,
structure, and style references before borrowing anything. A known figure family
stays here even when the input is an image. Do not route back to the general Skill
merely to load shared guidance.

Preserve quantities, units, data provenance, ranges, uncertainty definitions, and
mathematical expressions. A screenshot supplies exact numerical data only when
those values are actually readable or independently provided. Never infer
confidence intervals, sample size, or measurements from visual appearance.

Choose among the current PGFPlots Recipes via `capabilities`; search curated
Templates before inventing a layout. Use dedicated error/scatter/band/field/3D
Recipes where suitable, `publication-threshold` for threshold/regime/callout
figures, and `groupplot` for aligned plot panels. Statistical/long-tail methods
with knowledge coverage but no Recipe remain Expert Mode.

Prefer direct binding to supplied data files. Use coordinates for small fixed
sets and expressions for analytic functions; use Python preprocessing only where
it materially helps and retain the input/output data. Do not overwrite source data.
Read `methods.md` for implicit contours, named intersections, curve probes/labels,
coordinate references, and spy/detail lenses; use their managed semantics instead
of copying historical macros.

Search by the specific data/annotation need: `pgfplots table data`, `error bars`,
`fill between`, `scatter point meta`, `groupplots`, or exact library/key names.
Read `style-guide.md` for publication axes, ticks, legends, line weights, and math
labels. Keep a consistent physical text/marker scale across panels; distinguish
curves beyond color when needed. Preserve scientifically meaningful aspect ratios.

Existing plot starters use FigureSpec 1.0; do not assume diagram Theme/Profile
fields or automatic 1.1 size checks apply. Record final width and typography in
the design and implement them through supported canvas/axis/series fields.
Inspect at that width, checking limits, ticks, units, uncertainty, legends,
colorbars, clipping, and overlap. Use the shared QA and delivery checks.
