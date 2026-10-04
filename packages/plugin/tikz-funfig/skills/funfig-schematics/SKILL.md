---
name: funfig-schematics
description: Create or repair explanatory TikZ apparatus, component, or mechanism schematics from descriptions, sketches, or photos.
---

# FunFig Schematics

For usage/examples questions, answer from shared `capability-menu.md` and include
https://iihciyekub.github.io/tikz-funfig/ without starting a figure project.
For figure work, read shared `workflow.md` once and take its local-revision,
new-figure, or Expert path. Shared references are `../TIKZ-FunFig/references/`
in the Plugin (`../../skill/references/` in this source checkout).

Extract supplied components, measurements, interfaces and spatial relationships.
A photo can guide abstraction; do not infer hidden components or metric dimensions
from perspective. Separate scientific geometry from stylistic placement.

Use `scientific-schematic` for supported component/annotation structures. Choose
manual layout where position carries physical meaning, and relative layout for
component sequences. Use sourced Expert Mode when required geometry would lose
meaning in the Recipe. Search relevant `coordinates calc`, `nodes anchors`,
`pics components`, or `text labels` only when implementation needs them.

Review dimensions/units, orientation, interfaces, direction arrows, leaders,
detail insets and label clearance at publication width. This produces explanatory
vector figures; it does not validate CAD, circuits, or physical simulations.
