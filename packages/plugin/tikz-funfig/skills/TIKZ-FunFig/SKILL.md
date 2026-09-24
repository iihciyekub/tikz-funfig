---
name: tikz-funfig
description: Design, reproduce, and refine academic TikZ/PGFPlots figures from text, data, existing source, or reference images. Use for unclear or mixed figure types, reference-led redesign, and cross-family repairs; use a specialized FunFig Skill when the figure family is already clear.
---

# TIKZ-FunFig

Act as a scientific figure designer: understand the user's message, preserve its
meaning, choose a readable composition, and deliver editable LaTeX-native vector
artwork. Default to restrained, elegant academic typography and geometry;
respect an explicit manuscript style or requested visual treatment.

## Context-driven routing

The host agent selects Skills from their descriptions or explicit user invocation.
This Plugin does not execute Skills as functions or launch agents. Within a task,
read the appropriate sibling Skill and shared references yourself; the user need
not name a Skill, Recipe, theme, or schema. Explicit user instructions take priority.

Choose the family by the figure's meaning, independently of whether the input is
text, an image, data, or TeX:

| Main meaning | Specialized Skill | Stable starting point |
| --- | --- | --- |
| Axes, functions, measurements, uncertainty | `funfig-plots` | PGFPlots Recipes |
| Ordered steps, decisions, branches, feedback | `funfig-flowcharts` | `flowchart` |
| Layers, modules, containment, research framework | `funfig-frameworks` | `framework-diagram` |
| Concepts and labelled relationships | `funfig-relations` | `relation-diagram` |
| Apparatus, mechanism, spatial geometry | `funfig-schematics` | `scientific-schematic` |

Read only the relevant specialist. Stay here for mixed composition, migration,
reference interpretation with an unclear family, or repairs spanning families.
For a mixed figure, consult only the needed family guidance and coordinate one
composition and output directory. `groupplot` supports plot panels; it is not a
stable arbitrary diagram-plus-plot compositor. Use sourced Expert Mode when needed.
Specialists share the workflow below; do not bounce between entrypoints or ask the
user to choose an internal category.

## Shared design-to-delivery workflow

Read [workflow.md](references/workflow.md) once per task. It governs intent capture,
knowledge retrieval, mode choice, build, review, and stable delivery for all six
Skills. Carry forward existing decisions on revisions; load conditional references
only when they apply:

- Uploaded photograph, screenshot, sketch, or style/type reference:
  [reference-images.md](references/reference-images.md).
- New composition or substantial beautification:
  [composition.md](references/composition.md) and [style-guide.md](references/style-guide.md).
- New figure or existing design record:
  [design-contract.md](references/design-contract.md).
- Output location or source-of-truth questions:
  [output-policy.md](references/output-policy.md) and [schema-contract.md](references/schema-contract.md).
- Requirement outside stable Recipes:
  [expert-mode.md](references/expert-mode.md).
- Final-size review or layout repair:
  [visual-review.md](references/visual-review.md).
- Precise knowledge lookup:
  [reference-map.md](references/reference-map.md).
- Existing legacy TeX or promoted implicit/intersection/probe methods:
  [methods.md](references/methods.md). Start legacy extraction with `migrate-legacy`;
  inspect migration warnings and preserve scientific meaning before accepting it.
- Missing compiler, CJK fonts, or gnuplot:
  [dependencies.md](references/dependencies.md).

## Working contract

Use the current Skill's `scripts/funfig.sh` wrapper. Resolve its absolute path once
and keep the working directory at the user's active project; do not move into the
Plugin cache to execute it. Repository development can use `PYTHONPATH=src python3
-m funfig` instead. Query `capabilities`, `templates search/inspect`, and `kb search`
as needed instead of carrying a static Recipe catalog in these instructions.

For supported fields, edit `figure.funfig.json` and regenerate. Never repair a
managed figure only by patching generated TeX. For genuinely unsupported geometry,
Expert TeX remains the editable source with an explicit design record and provenance;
do not invent a FigureSpec Recipe to disguise it as stable behavior.

Normal new deliverables include `figure.design.json`, the canonical editable
source, `figure.tex`, PDF, and the mode-specific `.funfig` manifest; include SVG
only when requested. Existing filenames and explicit destinations take precedence.
Follow the shared output contract; do not scatter drafts or build files in the
project root. Figure artifacts belong to the user's project, never the Plugin cache.

Before delivery, view the rendered figure, repair content/layout problems, record
actual visual QA, and validate the design's delivery contract. Compilation alone
is insufficient. If an external dependency or unresolved semantic fact prevents
completion, describe that concrete limitation and retain useful editable work.

The Plugin knowledge tree, themes, profiles, and runtime are shared. Do not copy
them into each Skill or silently modify the installed Plugin while drawing. Raw
`sources/` and `references/legacy/` are development provenance and are not required
for installed operation. Reusable new capabilities belong in the source repository
and follow its schema, renderer, golden, knowledge, testing, and packaging rules.
