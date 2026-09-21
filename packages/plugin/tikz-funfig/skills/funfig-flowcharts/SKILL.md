---
name: funfig-flowcharts
description: Create and revise publication-quality academic flowcharts with TIKZ-FunFig. Use when the figure expresses ordered steps, decisions, branches, merges, loops, feedback, or a research/algorithm pipeline. Do not use for a conceptual framework whose main meaning is layered modules, or a generic concept relationship network without process semantics.
---

# FunFig Flowcharts

Model process meaning first, then layout. Do not infer missing decision outcomes or scientific causal meaning.
Use the packaged `scripts/funfig.sh` wrapper for capability queries, knowledge search, validation, build, and inspection.
Obey the shared TIKZ-FunFig output contract in `TIKZ-FunFig/references/output-policy.md`; do not choose a Plugin/Skill cache as an output directory.

## Workflow

1. Extract stable node IDs, labels, roles (`process`, `decision`, `terminal`, `data`), branch labels, and feedback edges.
2. Use Recipe `flowchart` and FigureSpec 1.1. Prefer relative layout for small flows and grid layout for regular multi-branch flows.
3. Query shared knowledge for `relative-positioning`, `flowchart-shapes`, `paths-routing`, `curved-edges`, and `diagram-layout-repair` as needed.
4. Keep arrow direction semantic; Theme changes must not change the process graph.
5. Validate, build, then run `inspect` and visually review the preview. Fix spacing/anchors/routes before shrinking text.

Use Expert TikZ Mode only when the requested notation cannot be expressed by the stable flowchart Recipe. Do not claim BPMN/UML conformance unless that notation is explicitly implemented.
