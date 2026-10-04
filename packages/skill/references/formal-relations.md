# Explicit formal relationship diagrams

Use only for requested specialist notation. Generic drawable shapes do not
establish formal conformance. Search sourced Expert knowledge when the stable
contract ends; formal ER and state-machine semantics are not implemented by
`relation-diagram`.

For a mathematical commutative diagram, inspect `commutative-diagrams` and its
compiled example. Preserve supplied objects, morphisms and claimed commuting
paths separately; drawing QA does not prove commutativity.

For a Petri net, use `petri-net`, FigureSpec 1.1 and inspect `petri-net-diagrams`.
Preserve supplied places, transitions, arcs, weights and initial marking.
Validate bipartition, directed weighted arcs and marking, then build/review via
the shared workflow. Use Expert TikZ for notation/layout outside the Recipe.
Reachability, liveness and boundedness require independent domain evidence.
