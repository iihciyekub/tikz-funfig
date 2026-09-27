# Expert pattern planner

Use these patterns to compose sourced Expert TikZ figures. They are planning
primitives, not new stable Recipes. For every selected pattern, retrieve current
knowledge/manual evidence and use the actual supported TikZ technique.

Choose the smallest set of patterns that explains the requested geometry. Prefer
named styles, coordinates, macros, and loops over long lists of unrelated offsets.
If repetition and symmetry can be represented directly by the stable generative
subset, use `generative-geometry.md` instead of treating every generated primitive
as an independent Expert pattern.

| Pattern | Use when | Typical techniques | Combine well with | QA focus |
| --- | --- | --- | --- | --- |
| `projected-wireframe` | sphere/dome/cylindrical projection or latitude/longitude mesh | elliptical arcs, clipping, scoped transforms | `layered-transparency`, `3d-coordinate-frame` | symmetry, hidden/visible arc hierarchy, projection consistency |
| `repeated-components` | many cells, particles, neurons, markers, repeated modules | `foreach`, reusable styles/pics, parameter lists | `layered-transparency`, `clipping-mask` | density, spacing, accidental regularity, overlap |
| `layered-transparency` | translucent regions/components with foreground/background order | PGF layers, opacity, draw/fill separation | most patterns | stacking order, grayscale readability, muddy overlap |
| `clipping-mask` | detail must stay inside a geometric boundary | `clip`, named paths, scopes | `projected-wireframe`, `repeated-components` | clipped labels/lines, boundary leakage |
| `intersection-geometry` | exact crossings/intersections determine placement | named paths, intersections, `calc` | `bezier-structure`, `annotation-leaders` | correct branch/intersection identity, numerical instability |
| `bezier-structure` | petals, anatomical contours, smooth custom boundaries | Bezier controls, symmetry, reusable path macros | `intersection-geometry`, `clipping-mask` | tangent continuity, mirrored consistency |
| `3d-coordinate-frame` | explicit 3D orientation or projected scientific geometry | `tikz-3dplot` or grounded coordinate transforms | `projected-wireframe`, `hidden-edge-logic` | camera convention, axis orientation, projected proportions |
| `hidden-edge-logic` | 3D solids need visible/hidden edge classification | face normals/visibility tests or explicit per-view classes | `3d-coordinate-frame` | front/back correctness at requested view; no edge receives conflicting classes |
| `procedural-layout` | deterministic pseudo-random or algorithmic arrangements | seeded PGF math, loops, reusable pics | `repeated-components` | reproducibility, painter order, collisions, excessive visual noise |
| `annotation-leaders` | callouts must point to geometry without crossings | anchors, bends, orthogonal/curved routes | any geometry pattern | leader-label clearance, unambiguous targets |
| `multi-region-composition` | several unlike zones share one figure without common axes | scopes, fit/background layers, named anchors | any pattern | reading order, alignment, visual hierarchy |
| `detail-inset` | magnified local geometry while preserving the whole | `spy` or explicit inset scope/connectors | plots/schematics | connector ambiguity, duplicate labels, inset scale |

## Planning record

Before authoring nontrivial Expert TeX:

1. List the required patterns in `routing.expert_patterns`.
2. Rewrite each pattern into one or two focused knowledge queries.
3. Retrieve a small relevant evidence set; record official/manual section IDs in
   `knowledge_sources` and supplementary cards/examples when useful.
4. Define shared parameters before detailed coordinates: canvas scale, major
   anchors, repeated component dimensions, line hierarchy, colors, and layers.
5. Implement patterns as reusable styles/macros/scopes, then compose them.

If more than about five independent patterns are needed, reassess whether the
figure should be split into panels or whether the route/family is wrong.

For `hidden-edge-logic`, explicit visible/hidden classes are acceptable for a
single fixed view. If the user needs an adjustable camera, derive or regenerate
visibility from the view; do not reuse one view's classifications. For
`procedural-layout`, set an explicit random seed and order overlapping components
back-to-front so deterministic generation is also visually deterministic.

## Anti-patterns

- Do not paste a large reference implementation and then edit incidental values.
- Do not use dozens of magic coordinates when a loop or named geometry exists.
- Do not treat a successful compile as evidence that the selected patterns are
  visually or scientifically correct.
- Do not promote a one-off pattern to a stable capability until it has schema or
  renderer support, a golden case, regression coverage, and documentation.
