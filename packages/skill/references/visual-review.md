# Visual acceptance and repair

Review the rendered image, not just TeX or the compiler log. `inspect` and
`expert-build` create previews; use the available image-viewing tool to open them.
Record actual observations with `qa` / `expert-qa`. Never mark a preview you have
not viewed as visually passed, and never edit a manifest to manufacture a pass.

## Acceptance order

1. **Meaning:** content, numbers, labels, directions, uncertainty, and group
   membership agree with the user's material. No starter/example facts remain.
2. **Reference alignment:** apply the assigned content/structure/style roles;
   preserve meaning during redesign and requested fidelity during reproduction.
3. **Final-size readability:** check the selected physical width, math/CJK glyphs,
   labels, line weights, markers, arrowheads, and panel lettering.
4. **Geometry:** no unintended text collision, clipping, edge through label/node,
   obscured data, ambiguous crossings, or group-border/title collision.
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

## Runtime limits

Structured 1.1 inspection provides Publication Profile width/text-risk estimates.
Older plot paths and Expert Mode do not yet offer identical automatic checks.
Use the physical dimensions in `figure.design.json` for manual final-size review
in every mode. Word boxes are approximate text measurements, not exact font-size
or full geometry/edge-collision analysis. Do not claim automatic aesthetic scoring.

Structured diagram width comes from node geometry, label sizes, and gaps;
`canvas.width` does not resize the diagram to that width. A Publication Profile
describes a width budget/projection, not an exact-size export guarantee. If the
user requires an exact physical width, measure the actual PDF/SVG and adjust
supported geometry (or an explicitly chosen inclusion scale) while preserving
readability. Do not report an exact width just because that number is in the spec.

The final `validate-design --delivery` checks files, source/build agreement and
recorded QA; it cannot certify that a human/agent really viewed the preview.
The Skill requires the actual visual inspection independently.
