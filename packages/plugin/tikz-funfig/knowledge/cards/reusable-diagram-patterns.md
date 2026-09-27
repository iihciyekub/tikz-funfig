# Reusable academic diagram patterns

Promote a repeated diagram behavior to a stable Recipe only after its semantics, knowledge card, executable example, schema fields, renderer behavior, and golden regression are all verified. One successful raw TikZ generation is not a stable capability.

Keep Skill reasoning flexible while keeping renderer output deterministic.

For dense mathematical figures, encode repeated structure in a
`structure_model` rather than copying visible primitives. The current Expert
generator path includes bounded expression sampling, turtle L-systems,
small-site Delaunay/Voronoi geometry, seeded Truchet tiling, and orthographic box edge classification
including shared-camera box overlap.
These are specific deterministic methods, not a general geometry solver.
For cyclic graph references, rank rendered candidate topologies and review the
visual result; pixel similarity alone does not establish scientific topology.

Choose patterns from semantics: sequence, branch/merge, feedback, layered modules,
containment, labelled topology, or meaningful spatial geometry. A reference image
can supply structure or style without supplying the user's facts. Record which
features to adopt and which content not to transfer in `figure.design.json`.
Translate natural-language design problems into focused knowledge queries before
selecting components. The design sidecar records intent and delivery; it does not
add renderer capabilities or turn source-extracted examples into stable Recipes.

For paper-width grids, `diagram.layout.auto_fit` estimates node widths and gaps.
It wraps English labels at word boundaries and can be overridden with explicit
text widths. Keep hypothesis labels clear of edge junctions and route feedback
outside the forward-reading path. Confirm both decisions in the final PDF;
automatic size and text-box checks do not prove an arrow avoids a label.

Source: TIKZ-FunFig architecture. Example: `reusable-pattern`.
