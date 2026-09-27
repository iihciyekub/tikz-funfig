# Generative geometry mode — long-tail / experimental

This subsystem is retained for existing managed figures and explicit specialist
requests. It is **not a default TIKZ-FunFig product surface**. Do not advertise
these generators in the main capability menu, do not route ordinary academic
framework/model/plot/flowchart tasks here, and do not add new generator families
without an explicit product-scope decision. See `scope-boundary.md`.

Use generative geometry for mathematically regular, densely repeated figures where
manual TikZ transcription would be brittle or visually inconsistent. This is an
Expert-mode implementation path: `figure.design.json` stores the structure model,
the runtime emits deterministic TikZ, and Expert build/QA remains authoritative.

## Implemented bounded subset

The runtime now supports a bounded but useful set of polar, Cartesian/isometric,
parametric/fractal, and projected-3D generators:

- `ring_nodes`: equally spaced nodes on a ring;
- `boundary_circle`: structural circle behind the graph;
- `complete_edges`: all pairwise chords for a ring;
- `circulant_edges`: chord classes defined by integer steps;
- `star_polygon`: repeated step connections around a ring;
- `center_node`: a node at or near the origin;
- `center_spokes`: edges from one center node to a ring.
- `line_nodes`: an evenly spaced node group along a line;
- `complete_bipartite_edges`: all cross-group edges between two node groups;
- `lattice_nodes`: nodes generated from an origin and two basis vectors;
- `lattice_edges`: deterministic neighbour steps on a lattice;
- `lattice_cells`: parallelogram cells or paired triangular cells induced by adjacent lattice nodes;
- `parametric_curve`: sampled `rose`, `lissajous`, Archimedean `spiral`, or bounded `expression` families;
- `koch_snowflake`: bounded-depth recursive Koch geometry;
- `l_system`: bounded deterministic turtle expansion with branch support;
- `point_nodes`: a small explicit set of distinct 2D sites;
- `delaunay_edges`: triangulation over `point_nodes`;
- `voronoi_cells`: Voronoi cells clipped to explicit bounds over `point_nodes`;
- `truchet_tiles`: seeded quarter-arc tiling on a shared affine grid;
- `projected_box`: an orthographic box with wireframe, hidden-dashed, or visible-only edges;
- `projected_prism`: a regular 3–64 sided prism extruded along z, with orthographic projection and view-derived visible/hidden edges.

Use `generative-render <design>` to emit deterministic TeX and
`generative-build <design>` to compile it with the design's official
`knowledge_sources`. The generated TeX is still inspectable and editable, but
regenerate from the design after structural parameter changes.

`parametric_curve` with `family: expression` takes `x` and `y` expressions in
`t`; arithmetic, constants `pi`/`e`, and common one-argument math functions
are allowed. Python attributes, imports, and unbounded results are rejected.
Sampling stays at or below 4000 points; singular samples fail the render.
`l_system` uses `F`/`G` to draw, `f`/`g` to move, `+`/`-` to turn, and `[`/`]`
to branch. Expansion is limited to 20,000 symbols and 10,000 drawn segments.
Mesh generation accepts 2–128 distinct sites; `voronoi_cells` requires finite
`[xmin,ymin,xmax,ymax]` bounds. `projected_box.visibility` may be `wireframe`,
`hidden_dashed`, or `visible_only`. Edge classification handles a single convex
box under an orthographic projection. Set `occlude_other_boxes: true` on each
box in a cluster to split edges at front-face occlusion boundaries. Cluster boxes
must share a projection basis and camera direction. Arbitrary solids and
perspective views need a separately checked Expert construction.
Set `camera_direction` explicitly when the intended front side is ambiguous;
it must be perpendicular to both projection rows.
`projected_prism` uses the same projection/camera convention. Its `sides`,
`radius`, `height`, and `rotation_deg` define congruent regular top/bottom
polygons and parallel extrusion edges; visibility is derived from adjacent face
normals. It intentionally does not yet support arbitrary polygon bases,
perspective projection, face fills, or inter-solid occlusion.
`truchet_tiles` supports `hash` or `checkerboard` orientation, a fixed integer
seed, and up to 1000 affine tiles. It does not implement aperiodic Penrose tiles.

For a cyclic graph reference with known ring-node count and approximate geometry,
run `generative-hypotheses <design> <reference.png> --limit 9`. It generates
complete, circulant-step, ring-plus-step, and optional center-spoke candidates,
compiles each one, compares normalized raster ink, and writes a ranked contact
sheet and `hypotheses.json` under `.funfig/hypotheses/`. Input may be an 8-bit
non-interlaced PNG or binary PGM. The reference and design must have matching
orientation and roughly matching proportions. Scores rank visual hypotheses;
inspect the top candidates before transferring a rule into the main design.

## Generator planning

1. Infer coordinate system and symmetry using `structure-inference.md`.
2. Express repeated geometry in `structure_model.generators`.
3. Put exact structural invariants in `structure_model.constraints`.
4. Let `visual_density` resolve dense-edge styling unless the reference requires
   explicit line weight or opacity.
5. Build, inspect at multiple scales, and use parameter search only for genuine
   aesthetic degrees of freedom.

Do not encode every edge as a separate generator. A complete, bipartite,
circulant, lattice-neighbour, fractal, or projection rule is the model; the
emitted primitives are only implementation details.

## Example

```json
{
  "structure_model": {
    "coordinate_system": "polar",
    "symmetry": {"group": "C16", "order": 16, "phase_deg": 90, "tolerance": 0.03},
    "generators": [
      {"id": "outer", "type": "ring_nodes", "parameters": {"count": 16, "radius": 5.0, "node_radius": 0.30, "phase_deg": 90}},
      {"id": "boundary", "type": "boundary_circle", "parameters": {"nodes": "outer"}},
      {"id": "chords", "type": "complete_edges", "parameters": {"nodes": "outer"}},
      {"id": "center", "type": "center_node", "parameters": {"radius": 0.14}},
      {"id": "spokes", "type": "center_spokes", "parameters": {"nodes": "outer", "center": "center"}}
    ],
    "constraints": ["outer nodes share one radius", "outer angular spacing is equal", "center remains at the origin"]
  }
}
```

The stable subset remains intentionally constrained. `lattice_cells` supports
parallelogram or diagonal-split triangular cells. The point-set mesh generators
do not implement weighted or periodic tessellations. For Penrose tilings,
arbitrary 3D solids beyond boxes/regular prisms, perspective occlusion, and unconstrained Python
expressions, use ordinary sourced Expert TikZ.
