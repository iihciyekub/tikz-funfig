---
name: funfig-schematics
description: Create and refine academic TikZ schematics from descriptions, sketches, apparatus photos, or reference figures. Use for components, scientific mechanisms, meaningful geometry, and labelled experiments.
---

# FunFig Schematics

Use the current Skill's `scripts/funfig.sh` wrapper from the user's project.
Shared references live in `../TIKZ-FunFig/references/` in the installed Plugin
(`../../skill/references/` in this source checkout). Read `workflow.md` once;
use its design, output, knowledge-retrieval, and visual-review contracts.
For any supplied image, also read `reference-images.md`; distinguish content,
structure, and style references before borrowing anything. A known figure family
stays here even when the input is an image. Do not route back to the general Skill
merely to load shared guidance.

Extract components, variables, spatial relationships, measurements, interfaces,
and supplied directionality. Preserve the scientific mechanism. A photograph can
guide an abstract apparatus schematic; do not infer hidden parts or metric
measurements from perspective. Separate scientific geometry from stylistic placement.

Use `scientific-schematic` for supported component/annotation structures. Prefer
manual layout where position carries physical meaning and relative layout for
component sequences. Use sourced Expert Mode for geometry, decorations, repeated
components, or mixed compositions beyond that Recipe; do not reduce meaningful
geometry to boxes merely to fit stable fields.

Query `coordinates calc`, `nodes anchors`, `arrows meta`, `pics components`, and
`text labels`, then exact relevant official examples/sections. Keep repeated
components reusable while exposing editable scientific parameters. Consult
`composition.md` for reading order and `expert-mode.md` only when needed.

Validate/build and view the preview. Check dimensions/units, coordinate orientation,
component interfaces, direction arrows, annotation leaders, detail insets, and
label clearance at final width. Ensure any abstraction still supports the intended
scientific explanation. Finish the shared QA and delivery checks.

This workflow produces explanatory vector figures, not a numerical geometry
solver, CAD model, circuit EDA validation, or physical simulation.
