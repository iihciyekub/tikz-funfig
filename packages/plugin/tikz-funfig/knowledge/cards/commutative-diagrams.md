# Commutative diagrams with matrix anchors

For a mathematical diagram, first record the objects, morphisms, arrow
directions, labels, and any claimed commuting paths. A visual square alone does
not establish that two compositions are equal; retain only relationships supplied
by the user or source material.

Use `matrix of math nodes` for regular object placement, then connect named cell
anchors with separately labelled arrows. Set row and column gaps in font-relative
units where the surrounding manuscript typography should control the diagram.
Use boundary anchors or projected coordinates when differently sized formulas
would tilt an intended horizontal or vertical arrow. Keep crossing and parallel
arrows explicit so their labels remain distinguishable at column width.

Current support: sourced Expert TikZ. A generic framework or relation Recipe
does not encode mathematical commutativity or morphism composition. Do not select
one merely because the diagram has four nodes and arrows.

Source: PGF/TikZ 3.1.11a matrix library, pp. 319–331, and node/edge syntax.
Example: `commutative-diagram`. TeXample's
[commutative diagram](https://texample.net/commutative-diagram-tikz/) motivated
this capability check; the bundled example below is independently authored.
