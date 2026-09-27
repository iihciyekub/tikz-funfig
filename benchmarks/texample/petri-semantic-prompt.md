# Petri semantic reconstruction probe

This is an independently authored **description-only** probe motivated by the
[TeXample Petri tutorial](https://texample.net/nodetutorial/). It is not a blind
redraw of that page and must not be scored as TeXample image fidelity.

Draw a single-column paper figure for a resource-gated task. Three places:
Waiting initially has two tokens, Resource initially has three, and Finished
has zero. The Execute transition consumes one Waiting token and two Resource
tokens; when it fires, it produces one Finished token and returns two Resource
tokens. Use a clean black-and-white style. Show non-unit arc weights and keep
the two opposing Resource arcs distinguishable.

Checks: place/transition bipartition; exactly four directed arcs; initial
marking (2, 3, 0); arc weights (1, 2, 2, 1); compiling vector PDF; legible at
the journal-single-column target width. Reachability/liveness are out of scope.
