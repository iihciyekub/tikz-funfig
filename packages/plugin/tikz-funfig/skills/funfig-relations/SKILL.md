---
name: funfig-relations
description: Draw academic concept, variable, path, and mathematical-model relationships in TikZ. Use for labelled constructs and user-supplied directed/undirected relationships; formal specialist notation is long-tail rather than the default route.
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
For a supplied moderation hypothesis, an edge may target another edge by ID with
`to_edge`; use this for a moderator-to-path arrow rather than drawing a misleading
direct effect from the moderator to an outcome construct. Keep the moderated path
itself explicit and review label clearance around the midpoint target.

Choose placement from the topology and label lengths. Search `edge labels quotes`,
`curved edges`, `self loops`, `nodes anchors`, and `arrows meta`. Read
`composition.md` for grouping and hierarchy. Use curved edges to disambiguate
parallel/self/feedback relationships; reconsider node placement before adding
many bends. A style reference must not introduce absent links or causal arrows.

Validate/build/inspect. Review every edge endpoint and label, unintended crossings,
self-loop clearance, repeated label ambiguity, and readability without relying
only on color. Complete shared visual QA and delivery checks at the target width.

Formal ER and state-machine semantics are not stable capabilities of the
relation-diagram Recipe. Search sourced Expert knowledge for long-tail notation;
never advertise formal conformance solely because its shapes can be drawn.
For a mathematical commutative diagram explicitly requested by the user, inspect `commutative-diagrams` and its
compiled example; record the supplied objects, morphisms, and claimed commuting
paths separately. For an explicitly requested Petri net with places, transitions, arcs,
weights, and initial marking, use `petri-net` FigureSpec 1.1 and inspect
`petri-net-diagrams`. Validate bipartition, direction/weights, and marking
against the supplied model, then build and review at publication width. Use
Expert TikZ for notation or layout outside that Recipe. Keep reachability,
liveness, and boundedness claims outside drawing QA unless separately established.
