# Structure inference for complex references

Use this reference when a supplied image contains dense repetition, strong
symmetry, many similar primitives, or hundreds of apparent edges. Do not begin by
transcribing every visible object. First infer the smallest generative structure
that can explain the image.

## Infer rules before objects

Ask, in order:

1. What coordinate system best explains the layout: Cartesian, polar, isometric,
   3D projection, layered graph, or freeform?
2. Is there a symmetry group or repeated spacing rule: cyclic, bilateral,
   translational lattice, recursive self-similarity, or shared 3D projection?
3. Which visible marks are primitive objects and which are generated repetitions?
4. Which connections are likely complete, circulant, star-polygon, lattice,
   nearest-neighbour, tree, or other rule-based families?
5. Which parameters control most of the appearance: count, radius, phase, step,
   spacing, line density, opacity, curvature, or projection?

For a ring of nodes with dense chords, test hypotheses such as complete graph,
circulant graph, selected chord classes, or superposed star polygons. For a mesh,
look for two basis vectors plus a small neighbour-step set. For repeated curves,
test whether one named parametric family explains the silhouette. For fractals,
look for recursive replacement rules. Prefer a small generator model over a long
list of manually copied primitives.

## Record a hypothesis, not certainty

For reference reproduction, record the inferred model in `structure_model` and
put uncertain interpretations in `content.assumptions`. If multiple plausible
models would look different, render small candidates and compare them before
committing to one. Do not claim that a mathematical topology is present unless
the reference or user supplies enough evidence.

For a single cyclic graph, first estimate ring-node count, radius, center, and
orientation from the image. Then use `generative-hypotheses` with that starter
design and an aligned PNG/PGM image to rank bounded edge-rule models. Review
the contact sheet and score margin. The command does not infer node locations
or general graph topology directly from arbitrary pixels.

## Measuring cyclic geometry

When ring-node centers can be estimated from the reference, use
`scripts/fit_polar_geometry.py` with a small JSON file of `[x,y]` centers. It fits
the common circle, reports cyclic spacing error, and suggests a `structure_model`
symmetry block. Use vision to identify candidate points; use the script to measure
and regularize them. Do not use image-processing output as the final artwork.

## Escalation rule

If more than roughly 20 visible marks can be described by fewer than 5 parameters
and one repeated rule, treat the figure as a generative-geometry candidate. If the
visible objects are semantically distinct or irregular, remain in ordinary Expert
composition instead.
