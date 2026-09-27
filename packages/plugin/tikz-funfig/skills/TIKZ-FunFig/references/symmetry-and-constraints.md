# Symmetry and structural constraints

Complex generative figures look polished when their invariants are explicit rather
than approximately maintained by manually entered coordinates.

Use `structure_model.symmetry` to record the intended regularity and
`structure_model.constraints` to state invariants such as:

- all outer nodes share one radius;
- angular spacing is equal;
- lattice nodes share one origin and two basis vectors;
- neighbour edges use one fixed integer step set;
- recursive fractal depth is global rather than locally patched;
- all projected solids share the same 3D-to-2D projection basis;
- the center node is exactly at the origin;
- repeated node sizes are identical;
- mirror pairs use the same parameters;
- one edge belongs to exactly one visible/hidden class;
- a seeded procedural layout is reproducible.

The runtime currently uses symmetry metadata as a design contract; not every
constraint is machine-solved. The agent must still compare the rendered result
with these invariants during visual QA. Prefer deriving coordinates from the
symmetry/generator model over manually repairing individual elements.

For reference reproduction, distinguish **model symmetry** from **raster noise**.
If a screenshot shows tiny spacing differences but the intended construction is
clearly cyclic or mirrored, fit the regular model and record the residual as a
tolerance rather than reproducing accidental pixel-level distortion.
