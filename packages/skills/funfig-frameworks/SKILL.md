---
name: funfig-frameworks
description: Create and revise publication-quality research frameworks, conceptual models, layered mechanism diagrams, and grouped system/module diagrams with TIKZ-FunFig. Use when the main structure is layers, modules, nested groups, or labelled cross-layer relationships. Do not invent causal relationships that the user did not supply.
---

# FunFig Frameworks

Translate the user's stated conceptual structure without adding scientific claims.
Use the packaged `scripts/funfig.sh` wrapper for capability queries, knowledge search, validation, build, and inspection.

## Workflow

1. Extract modules, layer/group membership, relationship direction, and labels separately from visual style.
2. Use Recipe `framework-diagram` and FigureSpec 1.1. Prefer grid layout for layers; use relative layout for irregular frameworks.
3. Use groups only for visual containment/hierarchy. Edges remain node-to-node in V1.
4. Query `fit-groups`, `background-layers`, `matrix-layout`, `nodes-anchors`, and `diagram-layout-repair` when needed.
5. Choose a journal Profile and Theme, validate/build, then inspect at final physical size.

When a framework contains a genuinely separate process flow, keep the semantic boundary clear rather than forcing every relation into flowchart notation.
