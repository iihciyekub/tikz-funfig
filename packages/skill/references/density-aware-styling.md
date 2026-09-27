# Density-aware styling

Dense mathematical figures need lower visual weight per primitive as complexity
increases. A geometrically correct complete graph can still fail visually if every
edge is drawn with ordinary diagram weight.

## Styling hierarchy

Use this draw order unless the reference requires another one:

1. structural boundary or background guides;
2. dense secondary edges;
3. emphasized primary structure;
4. nodes with opaque fill;
5. node outlines, center marks, and labels.

Drawing nodes last is important: white or background-colored node fills cleanly
mask dense chords and prevent lines from visually cutting through nodes.

## Automatic density

For generative geometry, prefer `visual_density.target: light` or `balanced` and
let the runtime derive edge line width and opacity from edge count. Override
`edge_line_width_pt` or `edge_opacity` only when a reference or publication target
justifies it. The design goal is approximately constant perceived darkness as the
number of edges grows, not constant line weight.

At final publication width, verify that:

- dense regions retain separable crossings rather than becoming a gray disk;
- nodes remain visually dominant over their incident edges;
- the structural boundary is visible but not stronger than the data/geometry;
- grayscale printing preserves the same hierarchy.

When the figure is still too dark, reduce edge opacity before shrinking nodes or
distorting geometry. When it is too weak, increase opacity before increasing line
width; thick dense edges produce muddy intersections quickly.

For lattices and tilings, keep cell fill substantially lighter than the edge
network. For fractal or parametric curves, preserve local segment continuity by
raising curve opacity before line width. For repeated projected solids, prefer a
single shared curve hierarchy rather than styling each box independently.
