---
name: tikz-funfig
description: Design, reproduce, and refine academic TikZ/PGFPlots figures, especially research frameworks, mathematical/variable relationships, 2D function/data plots, flowcharts, and basic academic schematics. Use for unclear or mixed paper figures and cross-family repairs; use a specialized FunFig Skill when the family is clear.
---

# TIKZ-FunFig

Act as an academic figure designer: understand the user's message, preserve its
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
| Social/business research framework, layers, constructs | `funfig-frameworks` | `framework-diagram` |
| Variables, mathematical models, concepts and labelled relationships | `funfig-relations` | `relation-diagram` |
| Basic apparatus/mechanism explanation | `funfig-schematics` | `scientific-schematic` |

Read only the relevant specialist. Stay here for mixed composition, migration,
reference interpretation with an unclear family, or repairs spanning families.
For a mixed figure, consult only the needed family guidance and coordinate one
composition and output directory. `groupplot` supports plot panels; it is not a
stable arbitrary diagram-plus-plot compositor. Use sourced Expert Mode when needed.
Specialists share the workflow below; do not bounce between entrypoints or ask the
user to choose an internal category.

Read [scope-boundary.md](references/scope-boundary.md) before expanding a task
outside the core academic-paper families. Existing long-tail Expert/generative
capabilities are not a reason to broaden the product automatically.

## Shared design-to-delivery workflow

Read [workflow.md](references/workflow.md) once per task. It governs intent capture,
knowledge retrieval, mode choice, build, review, and stable delivery for all six
Skills. Carry forward existing decisions on revisions; load conditional references
only when they apply:

- User asks what the Plugin can draw or how to use it, or invokes it without a
  figure request: [capability-menu.md](references/capability-menu.md).
- Uploaded photograph, screenshot, sketch, or style/type reference:
  [reference-images.md](references/reference-images.md).
- Complex, mixed, reference-led, or uncertain route selection:
  [routing.md](references/routing.md). Persist the selected route in the design
  record before implementing when the decision is nontrivial.
- User explicitly requests dense repetition, strong symmetry, radial/network/
  lattice structure, fractal/procedural geometry, or an existing managed figure
  already uses a compact generation rule:
  [structure-inference.md](references/structure-inference.md),
  [generative-geometry.md](references/generative-geometry.md), and
  [symmetry-and-constraints.md](references/symmetry-and-constraints.md). Infer the
  rule before drawing individual primitives.
- New composition or substantial beautification:
  [composition.md](references/composition.md) and [style-guide.md](references/style-guide.md).
- New figure or existing design record:
  [design-contract.md](references/design-contract.md).
- Output location or source-of-truth questions:
  [output-policy.md](references/output-policy.md) and [schema-contract.md](references/schema-contract.md).
- Requirement outside stable Recipes:
  [expert-mode.md](references/expert-mode.md) and
  [expert-patterns.md](references/expert-patterns.md). Build Expert figures from
  a small explicit pattern plan rather than ad-hoc coordinate accumulation.
- Final-size review or layout repair:
  [visual-review.md](references/visual-review.md).
- Dense-edge visual hierarchy or automatic line-weight decisions:
  [density-aware-styling.md](references/density-aware-styling.md).
- Structure is correct but a few numeric aesthetic parameters still need tuning:
  [parameter-search.md](references/parameter-search.md).
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
Treat `capabilities.product_scope=core` as the default product surface;
`long_tail` means technically retained but opt-in/specialist, not a prompt to
broaden the task.

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
