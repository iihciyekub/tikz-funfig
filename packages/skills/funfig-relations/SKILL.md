---
name: funfig-relations
description: Create and refine academic TikZ concept and relationship diagrams from text or reference images. Use for labelled directed or undirected links, parallel relationships, and self-relations.
---

# FunFig Relations

Use the current Skill's `scripts/funfig.sh` wrapper from the user's project.
Shared references live in `../TIKZ-FunFig/references/` in the installed Plugin
(`../../skill/references/` in this source checkout). Read `workflow.md` once;
use its design, output, knowledge-retrieval, and visual-review contracts.
For any supplied image, also read `reference-images.md`; distinguish content,
structure, and style references before borrowing anything. A known figure family
stays here even when the input is an image. Do not route back to the general Skill
merely to load shared guidance.

Preserve endpoints, direction, relationship labels, and route as separate choices.
Do not infer direction from sentence order when the user only says “related”.
Use `relation-diagram`, FigureSpec 1.1; default relations are undirected and
forward/backward/both require supplied meaning.

Choose placement from the topology and label lengths. Search `edge labels quotes`,
`curved edges`, `self loops`, `nodes anchors`, and `arrows meta`. Read
`composition.md` for grouping and hierarchy. Use curved edges to disambiguate
parallel/self/feedback relationships; reconsider node placement before adding
many bends. A style reference must not introduce absent links or causal arrows.

Validate/build/inspect. Review every edge endpoint and label, unintended crossings,
self-loop clearance, repeated label ambiguity, and readability without relying
only on color. Complete shared visual QA and delivery checks at the target width.

Formal ER, state-machine, and Petri-net semantics are not stable capabilities of
this Recipe. Search sourced Expert knowledge for actual long-tail notation needs;
never advertise formal conformance solely because its shapes can be drawn.
