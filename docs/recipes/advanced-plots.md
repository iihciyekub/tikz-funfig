# Advanced scientific plots

The advanced recipe family promotes the local 3D/field plotting notes into
stable FigureSpec semantics.

## `surface-plot`

Use `series.plot.kind: "surface"` or `"mesh"`. Analytic surfaces can bind
`data_sources[].domain` and `y_domain`; axes can declare `view`, `box3d`,
`colormap`, and `colorbar`. `shader` is a structured plot property.

Golden case: `examples/golden/surface-plot/`.

## `contour-plot`

Use `series.plot.kind: "contour"` with an explicit numeric `levels` array.
TIKZ-FunFig renders this through PGFPlots `contour gnuplot`, so the dependency
resolver requires gnuplot and shell escape for the managed build only.

Golden case: `examples/golden/contour-plot/`.

## `heatmap`

Use `series.plot.kind: "heatmap"`. Coordinate data uses triples `[x, y, meta]`;
`mesh_rows` and `mesh_cols` describe the matrix layout. A structured axis
colorbar explains the metadata scale.

Golden case: `examples/golden/heatmap/`.

## `quiver-field`

Use `series.plot.kind: "quiver"` with `u`, `v`, optional `w`, and
`scale_arrows`. Arrow styling may be supplied through `arrow_style`. Analytic
fields reuse the normal function data source and its x/y domains.

Golden case: `examples/golden/quiver-field/`.

## Regression rule

Every advanced golden case is re-rendered to deterministic TeX and actually
compiled. The committed TeX snapshot is the structural regression target;
the generated PDF is a build artifact and is not committed.
