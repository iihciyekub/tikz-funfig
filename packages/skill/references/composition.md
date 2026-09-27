# Composition decisions

Choose the composition before assigning detailed coordinates. Preserve supplied
geometry when position carries scientific meaning; otherwise let reading order,
label lengths, grouping, and target size determine placement.

## Layout by meaning

| Structure | Starting layout | Watch for |
| --- | --- | --- |
| Sequential process | aligned relative nodes | long labels, heterogeneous node sizes |
| Branch and merge | parallel lanes with explicit junctions | unclear outcomes or accidental crossings |
| Feedback | main path plus an exterior return route | loops crossing labels |
| Layered framework | aligned rows/columns and light groups | apparent causation introduced by arrows |
| Concept relationships | compact topology-aware placement | multiple labelled edges and false directionality |
| Physical schematic | meaningful named coordinates and anchors | loss of spatial/metric meaning |
| Data panels | aligned axes and shared visual encodings | inconsistent scales or duplicated legends |

For small clear requests choose one appropriate layout directly. For complex or
ambiguous compositions, compare a small number of genuinely different layouts
before investing in detail. Variants are useful when requested or when choosing
between layouts materially affects comprehension; do not make every user approve
multiple drafts. Several requested figures use one folder per stable figure ID
and consistent notation/style across the set.

## LaTeX academic character

Default to consistent TeX serif text and mathematical typesetting, clean vector
lines, restrained fills, balanced whitespace, and deliberate alignment. Match the
manuscript font when provided; use an installed CJK-compatible font/engine where
needed. Avoid web-card styling, gratuitous shadows, or unrelated pictograms unless
the user explicitly wants them. Elegant TikZ can include curves, geometry, repeated
components, and carefully used color; it need not force everything into boxes.

Give information a visual hierarchy: primary content, supporting structure,
annotations. Use a small coherent line-weight and font-size family. Use color to
encode meaning, with line patterns/shapes or labels where grayscale matters.
Theme choice changes appearance, never the graph or data.

Design at the intended physical width. A larger natural canvas later shrunk into
the same column may make text smaller; reflow, wrap, shorten only with preserved
meaning, or split panels when space is constrained. Do not silently switch to a
wider publication format. Global magnification is not a substitute for readability.
Diagram `canvas.width` is not a fit-to-width control: node geometry determines
the exported bounds. Measure the PDF for explicit exact-width requests; otherwise
use the selected column width as a readability/space budget.

Prefer semantic anchors, relative placement, named coordinates, and reusable
components to accumulated arbitrary offsets. Grid row/column gaps are coordinate
spacing; they do not guarantee visible clearance between unequal shapes.
For regular academic models with several comparable constructs, prefer
`diagram.layout.auto_fit=true`: it uses the selected Publication Profile width,
column count, and label-length estimates to choose a shared text width and safer
grid center spacing. Explicit node `text_width` and layout gaps remain overrides.
Use this for mediation/path/business-framework starters before hand-tuning widths.
Auto-fit nodes wrap at word boundaries without splitting ordinary English words;
review especially long words and formulas for overflow at the final width.

For moderation models, point the moderator to the supplied relationship itself
with `to_edge` rather than drawing an unintended moderator-to-outcome direct path.
Reserve edge-to-edge targets for semantics such as moderation/path annotation;
ordinary relationships should still terminate on construct nodes.

Search Templates by structure and inspect their edit contracts before reuse.
Compose compatible methods where useful. Repeated source examples are technical
references, not necessarily polished end-to-end compositions. Consult
`style-guide.md` for plot-specific axes, labels, intersections, and legend rules.
