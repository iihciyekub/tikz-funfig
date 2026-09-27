# Petri-net places, transitions, and tokens

Identify places, transitions, directed arcs, arc weights, and the initial token
marking before drawing. Places are circles and transitions are narrow bars or
boxes; token counts belong to places. Do not turn a general workflow step into
a Petri-net transition unless the user actually specifies Petri-net semantics.

The PGF/TikZ `petri` library supplies the visual primitives. Use named places
and transitions, label arcs and places deliberately, and check every arrow
against the declared pre/post relation. A rendered net does not by itself prove
reachability, liveness, boundedness, or conservation; those require separate
analysis if the user requests them.

Current support: the stable `petri-net` FigureSpec 1.1 Recipe preserves places,
transitions, initial non-negative integer markings, and positive integer arc
weights. The validator rejects place-to-place and transition-to-transition arcs,
duplicate directed arcs, and invalid identifiers/positions. The renderer uses
the PGF `petri` library for places and transitions. Markings of 0–9 use token
dots; counts of 10 or more are printed numerically because the PGF `tokens`
option does not handle ten or more correctly. Supply explicit x/y positions in
centimeters and bend antiparallel arcs so their directions and weights remain
legible. This contract does not analyze firing reachability, liveness, or
boundedness. Use sourced Expert TikZ for richer notation or a complex layout.

Source: PGF/TikZ 3.1.11a Petri-Net Drawing Library, pp. 745–749.
Example: `petri-net`. TeXample's
[Petri-net tutorial](https://texample.net/nodetutorial/) motivated this gap
review; the bundled example below is independently authored.
Stable golden: `examples/golden/petri-resource-loop/figure.funfig.json`.
