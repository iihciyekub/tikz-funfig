# Visual acceptance and repair

Review the rendered image, not just TeX or the compiler log. `inspect` and
`expert-build` create previews; use the available image-viewing tool to open them.
Record actual observations with `qa` / `expert-qa`. Never mark a preview you have
not viewed as visually passed, and never edit a manifest to manufacture a pass.

For reference-led work, define a small set of visual anchors before reviewing,
for example major extrema, group centroids, central axes, junctions, panel bounds,
or salient curve/shape intersections. Compare structure and relative placement;
do not optimize raw pixel similarity at the expense of meaning.

## Acceptance order

1. **Meaning:** content, numbers, labels, directions, uncertainty, and group
   membership agree with the user's material. No starter/example facts remain.
2. **Reference alignment:** apply the assigned content/structure/style roles;
   preserve meaning during redesign and requested fidelity during reproduction.
3. **Final-size readability:** check the selected physical width, math/CJK glyphs,
   labels, line weights, markers, arrowheads, and panel lettering.
4. **Geometry:** no unintended text collision, clipping, edge through label/node,
   obscured data, ambiguous crossings, or group-border/title collision.
   Check hypothesis labels at path junctions, whether feedback arrows stay
   outside the main path, and whether long English words break awkwardly.
5. **Design:** coherent typography, alignment, spacing, hierarchy, color encoding,
   and grayscale readability when appropriate.
6. **Delivery:** correct editable source and requested formats, current build/QA
   state, and no transient files among user-facing artifacts.

Machine warnings are evidence to investigate, not an aesthetic judgement.
Treat reported text overlap as a layout failure until resolved or demonstrated
by inspection to be intentional mathematical typesetting. If a proven false
positive cannot be represented by the current QA tool, report that limitation;
do not fabricate a clean machine pass. A passing machine check never replaces
visual review.

## Repair order

Repair the actual defect: semantic grouping/composition -> node/panel clearance
and text wrapping -> anchors/routes/label placement -> minor typography changes.
Increase natural size only if the final size constraint permits it. Prefer a
clearer arrangement over shrinking every label. Preserve scientific content;
move long explanations to a caption only where that preserves user intent.

After changing source, rebuild and inspect again. Review the complete image as
well as affected regions; local repairs can displace other content. Stop when
content, reference fidelity, requested style, and final-size readability satisfy
the task. If successive changes no longer improve a concrete remaining problem,
report that problem and the useful current artifacts rather than looping.

## Defect-led repair loop

For a nontrivial reference reproduction or substantial redesign, use a short
defect ledger for each review cycle:

```text
iteration: 2
defects:
- upper cluster too narrow relative to the reference anchors
- grid competes visually with primary components
repairs:
- increase upper-cluster horizontal spread
- reduce secondary grid line opacity/weight
```

Each defect must be observable in the current preview and each repair must target
that defect. Do not make unrelated cosmetic changes in the same cycle. Default to
three review/repair cycles; continue only when a concrete defect remains and the
previous cycle made measurable progress.

The runtime keeps review history across rebuilds. A failed review followed by a
repair and rebuild must remain visible in `qa.review_history`; use `repair_cycles`
as the count of failed review rounds rather than reconstructing it from memory.

Before passing, check all four layers:

1. semantic correctness;
2. geometry/clearance;
3. reference alignment or intended visual hierarchy;
4. readability at the target publication width.

For dense or generative figures, review at three scales: a small thumbnail for
global silhouette and balance, the normal preview for spacing/density hierarchy,
and a zoomed view for node masking, crossings, line joins, and local collisions.
If the structure is correct but the figure is too dark or too weak, repair visual
density or run a bounded parameter search instead of changing topology.

## Runtime limits

`inspect` now records one `size_check` contract for both major managed paths:
structured 1.1 diagrams use the Publication Profile target width/minimum text,
while 1.0 function/data plots use the explicit `canvas.width` plus the conservative
7.5 pt journal text baseline. The record includes natural PDF dimensions, target
source/width, scale-to-target, and projected dimensions. Expert Mode still needs
manual final-size interpretation from `figure.design.json`. Word boxes are
approximate text measurements, not exact font-size or full geometry/edge-collision
analysis. Do not claim automatic aesthetic scoring.

Structured diagram width comes from node geometry, label sizes, and gaps;
`canvas.width` does not resize the diagram to that width. A Publication Profile
describes a width budget/projection, not an exact-size export guarantee. If the
user requires an exact physical width, measure the actual PDF/SVG and adjust
supported geometry (or an explicitly chosen inclusion scale) while preserving
readability. Do not report an exact width just because that number is in the spec.

The final `validate-design --delivery` checks files, source/build agreement and
recorded QA; it cannot certify that a human/agent really viewed the preview.
The Skill requires the actual visual inspection independently.
