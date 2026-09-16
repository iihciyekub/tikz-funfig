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
- `axes` — axis labels, ranges, ticks, grid, legend position.
- `data_sources` — named function/file/coordinate/gnuplot sources.
- `series` — visual series bound to a named data source.
- `regions` — highlighted rectangles or fill-between regions.
- `annotations` — points, labels, guide lines, intersections.
- `panels` — multi-panel series bindings.
- `diagram` — named nodes and edges for TikZ diagrams.
- `outputs` — stable artifact basename and intermediate retention policy.

## Data binding

A series must refer to a `data_sources[].id`, never to an implicit positional data source. Panels refer to stable `series[].id` values. Diagram edges refer to stable node IDs. Intersection annotations refer to named series paths.

This binding rule is what makes later small edits stable: data, style, annotation, and layout remain separate concerns.

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

## Change rule

When a user asks for a supported change, edit the FigureSpec and regenerate. Only edit generated `.tex` directly when diagnosing the renderer or when handling a legacy figure not yet represented by a recipe.

