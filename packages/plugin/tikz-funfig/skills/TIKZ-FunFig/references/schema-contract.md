# FigureSpec and artifact contract

## Source of truth

For TIKZ-FunFig-managed figures, `figure.funfig.json` is the editable source of truth. `figure.tex` is deterministic generated source and `figure.pdf` is the compiled artifact.

The canonical JSON Schema lives in the source repository at:

`tikz-funfig/schemas/figure-spec.schema.json`

## Core FigureSpec sections

- `schema_version` — contract version.
- `id` — stable figure identifier.
- `recipe` — renderer/behavior recipe.
- `kind` — `pgfplots` or `tikz`.
- `canvas` — physical figure dimensions and border.
- `engine` — LaTeX and external compute engine preference.
- `axes` — axis labels, ranges, ticks, grid, legend position, and the axis presentation preset.
- `axes.preset` — `publication-offset` or `standard`. Supported ordinary 2D
  paper recipes default to `publication-offset` when omitted; advanced
  surface/contour/heatmap/quiver recipes default to `standard`.
- `axes.view`, `axes.box3d`, `axes.colormap`, `axes.colorbar` — structured 3D/categorical-color presentation.
- `data_sources` — named function/file/coordinate/gnuplot sources.
- `series` — visual series bound to a named data source.
- `series.plot` — structured line/scatter/surface/mesh/heatmap/contour/quiver rendering semantics.
- `series.scatter` — scatter semantics (`scatter src`, metadata binding, optional labels).
- `series.error_bars` — structured x/y uncertainty with explicit, relative, fixed, or asymmetric bindings.
- `regions` — highlighted rectangles or fill-between regions.
- `annotations` — points, labels, guide lines, intersections.
- `panels` — multi-panel series bindings.
- `group` — structured groupplot columns, spacing, and edge-only tick/label placement.
- `diagram` — named nodes and edges for TikZ diagrams.
- `outputs` — stable artifact basename and intermediate retention policy.

## Data binding

A series must refer to a `data_sources[].id`, never to an implicit positional data source. Panels refer to stable `series[].id` values. Diagram edges refer to stable node IDs. Intersection annotations refer to named series paths.

Fill-between regions bind to stable `series[].name_path` values. Explicit error
bars bind column names through `series.error_bars`; scatter metadata binds through
`series.scatter.meta`. These relationships are validated before rendering.

This binding rule is what makes later small edits stable: data, style, annotation, and layout remain separate concerns.

For advanced PGFPlots figures, keep geometry/compute semantics structured:

- `series.plot.kind: surface|mesh` controls 3D surfaces without raw plot options.
- `series.plot.kind: contour` binds an explicit `levels` array and activates the gnuplot dependency automatically.
- `series.plot.kind: heatmap` treats coordinate triples as `[x, y, meta]` and can bind matrix rows/columns.
- `series.plot.kind: quiver` binds `u`, `v`, optional `w`, and `scale_arrows` expressions.
- `data_sources[].y_domain` is the second analytic domain for 3D sampling.

## Artifact responsibilities

### Preserve

- `figure.funfig.json`
- explicit source data under `data/`
- generated `figure.tex`
- final `figure.pdf`
- `.funfig/manifest.json`

### Disposable

- `.funfig/build/`
- `.aux`, `.log`, `.fls`, `.fdb_latexmk`, and similar TeX intermediates
- PGFPlots `.gnuplot` and generated `.table` files

The build system may remove disposable artifacts after a successful build. It must not remove FigureSpec, source data, generated TeX, or the final PDF.

## Project output location

The Plugin runtime is an engine, not a storage destination. Stable figure
artifacts must be written under the user's active project. Resolution order is:

1. explicit user-specified directory;
2. an existing managed figure directory for an update;
3. `<project-root>/figures/<figure-id>/` for a new figure when no directory was specified.

`funfig init --project-root <root> --id <id> --recipe <recipe>` implements the
third rule. Never create user figure artifacts under `~/.codex/plugins/cache/`
or another Plugin installation directory.

## Publication-oriented structured fields

The `publication-threshold` recipe adds structured semantics for recurring patterns found in the local publication figures. Prefer these fields over opaque raw TikZ options when they apply:

- `axes.title`
- `axes.preset`
- `axes.axis_line_shift`
- `axes.tick_precision`
- `axes.legend.{position,at,anchor,columns,font,cell_anchor}`
- annotation `font`, `rotate`, `arrow`, `arrow_anchor`, and `arrow_style`
- annotation style `fill`, `draw`, `mark_size`, `opacity`
- `point`/`intersection` annotation `label_style` for an independent label style

For point and intersection labels, `style` controls the marker. When `label_style`
is omitted, only marker `style.color` carries over to label text; marker fills,
borders, and opacity do not override the publication label backing. Set
`label_style` explicitly to customize the label fill, border, text color, or
opacity. Other annotation types continue to use `style` for their text.

Point callout arrows without `arrow_anchor` are drawn before the label so its
backing masks the line under the text. An explicit `arrow_anchor` binds the
connector to that label node anchor. Intersection connectors default to the node
boundary and also honor an explicit `arrow_anchor`.

An intersection callout should remain bound to `path_a` and `path_b`, rather than being converted into a hard-coded coordinate unless the scientific meaning is explicitly a fixed coordinate.

## Legacy migration state

`funfig migrate-legacy` produces a draft FigureSpec. Migration provenance belongs under `metadata.migration` and should include the legacy source path, detected feature counts, and warnings for semantics that were not safely inferred. Keep `status: "draft"` until those warnings have been reviewed.

A compiling migration draft is not automatically a completed migration.

## Change rule

When a user asks for a supported change, edit the FigureSpec and regenerate. Only edit generated `.tex` directly when diagnosing the renderer or when handling a legacy figure not yet represented by a recipe.
