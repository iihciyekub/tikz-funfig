---
name: funfig-frameworks
description: Create and refine academic TikZ research frameworks and module architectures from text or reference images. Use for layers, nested groups, conceptual models, and labelled relationships between modules.
---

# FunFig Frameworks

Use the current Skill's `scripts/funfig.sh` wrapper from the user's project.
Shared references live in `../TIKZ-FunFig/references/` in the installed Plugin
(`../../skill/references/` in this source checkout). Read `workflow.md` once;
use its design, output, knowledge-retrieval, and visual-review contracts.
For any supplied image, also read `reference-images.md`; distinguish content,
structure, and style references before borrowing anything. A known figure family
stays here even when the input is an image. Do not route back to the general Skill
merely to load shared guidance.

Extract modules, layer/group membership, relationship direction, and labels
separately from visual style. Do not add scientific or causal claims. A reference
architecture may guide organization without supplying the user's module names,
connections, or results.

Use `framework-diagram` with FigureSpec 1.1. Search Templates for the desired
layer/group structure. Prefer grid layout for regular layers and relative layout
for irregular structures or varying label lengths. Groups express containment;
V1 edges remain node-to-node, not group endpoints. Read `composition.md` to set
a clear reading order, hierarchy, and whitespace before detailed coordinates.

Search `fit groups`, `background layers`, `matrix layout`, `nodes anchors`, and
`diagram layout repair`. Keep group fills lighter than primary modules and group
titles clear of borders and connectors. Align repeated roles, not just box centers.
Choose a restrained Theme/Profile and preserve supplied manuscript typography.

If a framework includes a separate process or data panel, consult only that
family's guidance; do not force all relations into process notation. Arbitrary
mixed panels and specialized ML components may require sourced Expert Mode.

Validate/build/inspect and review content, containment, cross-layer connections,
long labels, group nesting, and visual balance at final width. Complete the shared
QA and delivery checks. A Theme change must not change the conceptual structure.
