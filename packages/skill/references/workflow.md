# Shared figure workflow

Use for actual figure creation, revision, or implementation planning. For help
only, answer using `capability-menu.md`, include the Example Gallery link, and
stop. Explicit user instructions and the requested scope override workflow
defaults. Make routine visual choices yourself; ask only for missing facts or
conflicting references that materially affect meaning or requested fidelity.

## Common working contract

Use the current Skill's `scripts/funfig.sh` at its resolved absolute path while
working in the user's project. Source development may use `PYTHONPATH=src python3
-m funfig`. The Plugin runtime/knowledge are shared, read-only drawing resources;
outputs belong in the user's project, never the Plugin cache.

Preserve supplied facts, data, units, relationships, IDs, and scientific meaning.
A style/layout example supplies appearance, not new evidence or labels.
Structured `figure.funfig.json` is authoritative: edit it and regenerate rather
than patching generated TeX. In Expert Mode, authored TeX (or a managed
`structure_model`) is authoritative. Do not invent a Recipe to hide unsupported
semantics. Normal new delivery includes `figure.design.json`, editable source,
TeX, PDF, and the mode-specific `.funfig` manifest; add SVG when requested.
Existing filenames and explicit destinations take precedence. Read
`output-policy.md` / `schema-contract.md` when initializing or changing output
placement, formats, or source representation.

## Choose the amount of work

- **Local revision/repair:** read the existing source and design first. Preserve
  its mode, content, IDs, data bindings, and location. Update only affected design
  choices; retrieve knowledge only for an actual gap. Rebuild and review the current
  result. Add a minimal design record when adopting managed delivery for an older
  figure; do not migrate unrelated figures.
- **New figure/reproduction/redesign:** capture the communication goal, facts,
  reference roles, width, language, and formats in `figure.design.json` using
  `design-contract.md`. For a new composition, consult `composition.md`; use
  `style-guide.md` for typography/axes choices. Choose a compatible stable Recipe
  or Template without distorting meaning.
- **Unsupported geometry/notation/composition:** consult `routing.md`, name the
  concrete gap in the best Recipe, then follow `expert-mode.md`. Styling alone
  is not a reason to abandon an adequate structured source.

A supplied `TFF-xxxx` is a direct lookup: follow `example-gallery.md` before
fuzzy retrieval. Keep the requested alias in provenance while using its canonical
source. For any uploaded image, follow `reference-images.md` and actually view it.

## Retrieve only what is missing

Query `capabilities` when support is uncertain or the task introduces a new
feature. Prefer core Recipes and curated Templates, then verified cards and
relevant official examples/manual sections. Inspect exact hits with `kb show
<id> --json`; source-extracted examples are not stable Recipes.
Rewrite long requests into focused structural/technical queries, for example
`relative positioning`, `fit groups`, `paths routing`, or `edge labels quotes`.
Inspect only enough relevant material to resolve the gap; record the IDs used.
A local edit with known support need not repeat Template or knowledge searches.

Load conditional detail only when relevant:

| Need | Reference |
| --- | --- |
| Dense repetition or symmetry explicitly requested, or existing generative work | `structure-inference.md`, then relevant `generative-geometry.md` / `symmetry-and-constraints.md` |
| Dense-edge visual weight | `density-aware-styling.md` |
| Structure correct; numeric aesthetics need tuning | `parameter-search.md` |
| Exact knowledge location | `reference-map.md` |
| Legacy migration or promoted implicit/intersection/probe methods | `methods.md` |
| Missing compiler, CJK font, or gnuplot | `dependencies.md` |

Infer a compact repetition rule yourself when applicable; do not ask the user
to select an internal generator. Preserve topology and scientific parameters
while tuning appearance. Long-tail geometry remains subject to `scope-boundary.md`.

## Build and finish

For new structured work, initialize in the user's project with `init --id <id>
--recipe <recipe>` and replace all starter content. Implement design targets in
supported FigureSpec fields; `optimize --design` binds the design width/text baseline.
Common process/framework/relation starters use measured auto placement; physical
schematics retain their manual coordinates with measurement enabled.
For adjustable diagrams or reported layout defects, read `smart-layout.md` and
use measured optimization before final image review. Other design prose remains
an interpretation contract, not automatic renderer configuration.
Validate the design and spec, then `build` and `inspect`. Expert work uses the
build/provenance commands in `expert-mode.md`.

Follow `visual-review.md`: view the current preview at target width, check content,
references, readability and clearance, and repair observed defects. Rebuild after
source changes; record `qa` / `expert-qa` only after viewing that current output.
Compilation and recorded machine checks do not establish visual acceptance.
Finish with `validate-design <dir>/figure.design.json --delivery`.

Deliver the preview and requested editable artifacts with a short description of
material choices or limitations. Continue until the requested result and current
build/review/delivery checks agree; if a concrete dependency or unresolved fact
blocks completion, retain useful work and identify it. Planning-only requests
stop at the requested plan; no files or compilation are required.
