---
name: funfig-relations
description: Create and revise publication-quality concept/entity relationship diagrams with TIKZ-FunFig. Use for labelled directed, undirected, or bidirectional relationships, curved parallel relations, self-relations, and small academic concept networks. Do not use for process flows just because arrows are present, and do not claim formal ER/UML semantics unless implemented.
---

# FunFig Relations

Preserve relation semantics explicitly: endpoints, direction, label, and route are independent fields.
Use the packaged `scripts/funfig.sh` wrapper for capability queries, knowledge search, validation, build, and inspection.
Obey the shared TIKZ-FunFig output contract in `TIKZ-FunFig/references/output-policy.md`; do not choose a Plugin/Skill cache as an output directory.

## Workflow

1. Extract concept/entity nodes and every supplied relationship. Do not infer direction from sentence order when the user says only “related”.
2. Use Recipe `relation-diagram` and FigureSpec 1.1. The default relation is undirected; set forward/backward/both only when meaning is supplied.
3. Query `edge-labels-quotes`, `curved-edges`, `self-loops`, `nodes-anchors`, and `arrows-meta` as needed. Prefer stable/compiled project knowledge; consult matching official source examples for syntax variants before manual-wide fallback.
4. Use curved edges only to resolve ambiguity or represent parallel/feedback relations; reconsider layout before adding many bends.
5. Validate/build/inspect and ensure labels remain readable without relying on color alone.

Formal ER, state-machine, and Petri-net notation remain future Recipe capabilities and are not implied by this Skill.
