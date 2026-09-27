# TeXample capability audit (2026-09-27)

The [TeXample alphabetical list](https://texample.net/list/) contained 417 posts
when inspected. Its categories include 123 diagram posts, 110 mathematics posts,
43 plot posts, 44 electrical-engineering posts, and 12 animation posts; a post
can belong to more than one category. The 30 entries in `audit.json` are a
purposeful cross-category sample, not a random sample or a claim about all 417.

Each entry was read at its linked page for its intended figure and required
techniques/packages. The assessment is an **architectural route assessment**, not
a completed redraw or visual pass:

- `structured_candidate`: current stable FigureSpec/Recipe appears sufficient
  for the underlying paper-figure intent, subject to an actual build and QA.
- `expert_candidate`: current TikZ/PGFPlots knowledge and sourced Expert Mode
  appear sufficient, but no stable structured Recipe exists.
- `capability_gap`: the Plugin lacks a reliable route for a required specialized
  semantic contract, dependency, geometry solver, input data, or output format.
  A skilled human may still draw such a figure with TikZ.
- `outside_scope`: not a scientific figure deliverable in this Plugin.

Count in this selected sample: 5 structured candidates, 15 Expert candidates,
9 capability gaps, 1 outside scope. These are not success rates. No TeXample
code, artwork, or PDF is bundled here. TeXample marks the site CC BY-SA 4.0;
any future redistributed adaptation must preserve appropriate attribution and
license terms. These links are evaluation references, and the two new compiled
knowledge examples in `knowledge/examples/` are independently authored.

Continue measuring the in-scope entries with separate image-only or
description-only prompts, hidden original TeX, and recorded semantic fidelity,
geometry, target-width readability, compilation, and repair cycles. Do not
promote a candidate to "supported" based on the source review alone.

The first follow-up is `petri-semantic-prompt.md`: an independently authored
description-only probe motivated by the TeXample Petri tutorial. Its measured
result is in `followup-results.json`. Since the source page was already read in
the architectural audit, this probe is **not** a blind image reproduction or a
match to the TeXample figure. The prior `audit.json` remains the dated baseline;
the follow-up records the new stable capability separately.

`scenario-tree-blind/` records the first image-only blind reproduction that
produced a concrete renderer gap. The initial structured build compiled and
preserved the visible formulas/topology, but horizontal-only edge labels
overlapped nodes. That failure promoted `diagram.edges[].label_sloped` into the
1.1 schema/renderer with a dedicated golden case; the rebuilt scenario tree then
passed machine and visual QA. This benchmark keeps the authored FigureSpec and
design record, not the reference artwork or source TeX.

`blind-cases.json` fixes two image-only prompts: the structured scenario tree
and an Expert energy-level schematic. `energy-level-diagram-blind/` contains
our independently authored TeX and design record. The dated
`blind-results-2026-09-27.json` reports **2/2 passing** after build, inspection,
and agent visual review: 169.12 mm against a 178 mm double-column budget for
the tree, and 66.8 mm against an 88 mm single-column budget for the energy
diagram. The tree took one recorded failed-review/repair round. This is a
two-case result, not an estimate of performance across TeXample. The review
rubric records visible meaning, geometry, readability, and reference alignment;
it does not claim pixel similarity or independent human grading.

`regular-prism-followup.json` records promotion of a reusable 3D subset motivated
by the earlier regular-hexagonal-prism audit entry. The new `projected_prism`
generator is not a reproduction of that TeXample source: it is an independently
implemented regular-prism model with bounded side count, orthographic projection,
and automatic visible/hidden edge classification. A deterministic six-sided
golden case locks the behavior. Perspective, arbitrary polyhedra, face filling,
and inter-solid prism occlusion remain outside this stable subset.
