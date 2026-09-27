# Parameter search for visual refinement

Use bounded parameter search when the structure is already correct but a few
continuous aesthetic parameters still control visual quality. Do not search over
semantic content or topology.

Good search parameters include edge opacity, edge line width, node size, spacing,
curve tension, label offsets, or a projection angle. Bad search parameters include
scientific values, category membership, or relationships that the user supplied.

## Coarse-to-fine workflow

1. Keep the current structure fixed.
2. Put 1-2 numeric parameters in `search_space`, normally with 3 candidate values
   each. Keep the Cartesian product small; 9 variants is a useful default.
3. Run `generative-variants <design> --limit 9`.
4. Open `.funfig/variants/contact-sheet.png` and compare the whole grid at once.
5. Select the strongest region of the search space, update the main design, then
   rebuild and perform normal visual QA.
6. If necessary, run one narrower search around the selected values.

Example:

```json
{
  "search_space": [
    {"path": "visual_density.edge_opacity", "values": [0.28, 0.36, 0.44]},
    {"path": "visual_density.edge_line_width_pt", "values": [0.18, 0.24, 0.30]}
  ]
}
```

Do not treat the contact sheet as final QA. It is a selection aid. Transfer the
chosen values into the canonical design, rebuild the main figure, then inspect it
at target size and record the actual QA result.
