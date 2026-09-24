---
name: funfig-flowcharts
description: Create and refine academic TikZ process diagrams from text or reference images. Use for ordered steps, decisions, branches, merges, and feedback; layered concepts without process meaning belong to frameworks.
---

# FunFig Flowcharts

Use the current Skill's `scripts/funfig.sh` wrapper from the user's project.
Shared references live in `../TIKZ-FunFig/references/` in the installed Plugin
(`../../skill/references/` in this source checkout). Read `workflow.md` once;
use its design, output, knowledge-retrieval, and visual-review contracts.
For any supplied image, also read `reference-images.md`; distinguish content,
structure, and style references before borrowing anything. A known figure family
stays here even when the input is an image. Do not route back to the general Skill
merely to load shared guidance.

Model process meaning first: stable node IDs, readable labels, process/decision/
terminal/data roles, branch outcomes, merges, and feedback. Do not infer missing
decision outcomes or scientific causal meaning. Use Recipe `flowchart`, FigureSpec
1.1, and a suitable Theme/Profile.

Prefer relative layout for small flows, variable-width labels, and decision/data
nodes: TikZ positioning preserves border-to-border clearance. Use grid layout for
regular parallel lanes with comparable node sizes; `row_gap` / `column_gap` are
coordinate spacing, not guaranteed clearance between heterogeneous boxes. Read
`composition.md` when selecting a new layout.

Search `relative positioning`, `flowchart shapes`, `paths routing`, `curved edges`,
and `diagram layout repair`. Use explicit routes/anchors to keep feedback outside
the main reading path. Preserve graph meaning when reorganizing lanes or styling.
A plain-language need such as “汇合后再分支” should become focused merge/branch and
routing queries, not just an unsegmented search sentence.

Validate/build/inspect and view the preview. Treat unintended text overlap as a
layout failure; machine checks alone do not establish acceptance while visual
review is pending. Fix spacing, anchors, and routes before shrinking text. Increase
canvas size only when the target publication width permits it; otherwise reflow.
Check every arrow direction, branch label, merge, and endpoint at final size, then
record QA and verify delivery with the shared workflow.

Use sourced Expert Mode for required notation outside this Recipe. Do not claim
BPMN/UML conformance unless that notation is explicitly implemented.
