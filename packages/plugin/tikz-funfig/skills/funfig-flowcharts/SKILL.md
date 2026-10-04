---
name: funfig-flowcharts
description: Create or repair TikZ process diagrams with ordered steps, decisions, branches, merges, or feedback. A branching layout alone is not a process.
---

# FunFig Flowcharts

For usage/examples questions, answer from shared `capability-menu.md` and include
https://iihciyekub.github.io/tikz-funfig/ without starting a figure project.
For figure work, read shared `workflow.md` once and take its local-revision,
new-figure, or Expert path. Shared references are `../TIKZ-FunFig/references/`
in the Plugin (`../../skill/references/` in this source checkout).

Represent supplied process order, node roles, branch outcomes, merges, and
feedback with Recipe `flowchart`, FigureSpec 1.1. Do not turn a purely associative
or layered topology into a process; use relations or frameworks for that meaning.

Choose relative layout for varying label sizes and decision/data shapes; use
regular grids for comparable parallel lanes. Grid gaps are coordinate spacing,
not guaranteed border clearance. Use explicit routes/anchors for return paths.
When needed, search `relative positioning`, `flowchart shapes`, `paths routing`,
or `diagram layout repair`; read `composition.md` for a new arrangement.

Review arrow direction, branch labels, merges and endpoints at final size.
Repair spacing, wrapping, anchors and feedback routes before reducing text size.
For diagonal labels, `label_sloped` is supported; judge clearance in the preview.
Use sourced Expert guidance for required notation beyond this Recipe; shapes
alone do not establish BPMN/UML conformance.
