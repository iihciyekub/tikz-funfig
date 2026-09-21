---
name: funfig-schematics
description: Create and revise publication-quality scientific schematics with TIKZ-FunFig. Use for experiments, mechanisms, components, coordinates, inputs/outputs, directional effects, and lightweight scientific geometry that is primarily a labelled schematic rather than a data plot. Do not treat this as CAD, circuit EDA, or a numerical geometry solver.
---

# FunFig Schematics

Use Recipe `scientific-schematic` for stable component/annotation structures and Expert TikZ Mode for carefully sourced long-tail geometry or decoration features.
Use the packaged `scripts/funfig.sh` wrapper for capability queries, knowledge search, validation, build, inspection, and sourced Expert Mode.

## Workflow

1. Extract components, named variables, spatial relationships, measurements, and supplied directionality. Never alter the scientific mechanism.
2. Prefer manual layout when coordinates carry scientific/spatial meaning; use relative layout for component sequences.
3. Query `coordinates-calc`, `nodes-anchors`, `arrows-meta`, `pics-components`, and `text-labels` as needed.
4. Keep repeated visual components reusable, but do not hide editable scientific meaning inside opaque macros.
5. Validate/build/inspect; confirm labels, arrows, and component boundaries at the journal Profile size.

For capabilities outside FigureSpec, search the official manual corpus first, record source IDs/pages, then use `expert-build`. A raw result remains Expert Mode until promoted through Schema/Recipe/golden tests.
