# Scientific series recipes

The second stable recipe family is distilled from the local PGFPlots/TikZ memo
examples rather than from one manuscript figure. It deliberately shares the
same `data_sources` and `series` binding model so capabilities can be composed.

## `error-bar`

Use `series.error_bars.x` / `.y` to define uncertainty. Supported modes are:

- `explicit` — absolute values bound to `column`, `plus`, `minus`, or `expr`;
- `explicit_relative` — explicit relative values;
- `fixed` — one absolute value for all points;
- `fixed_relative` — one relative value for all points.

Asymmetric error bars bind `plus` and `minus` independently. The renderer emits
PGFPlots `error bars/.cd` and the corresponding table column bindings.

## `scatter-plot`

Set `series.plot` to `scatter` and configure `series.scatter`. For file data,
`scatter.meta` binds a table column to `meta`. `scatter.source` maps to PGFPlots
`scatter src`; numeric metadata can be made readable with `axes.colorbar`.

The golden case demonstrates `scatter src=explicit`, a `score` metadata column,
and a labeled right-side colorbar.

## `confidence-band`

Create upper/lower series with stable `name_path` values, then bind a region:

```json
{
  "type": "between",
  "path_a": "upper",
  "path_b": "lower"
}
```

The validator rejects missing path bindings. Optional `domain` maps to PGFPlots
soft clipping for partial bands.

## `groupplot`

Panels continue to bind named series. Layout belongs in the top-level `group`
object: columns, horizontal/vertical separation, and edge-only label/tick rules.
Global axes are emitted once at the group container; they are not repeated on
every panel. A panel receives local axis options only when it explicitly defines
an `axes` override.

## Regression contract

Canonical examples are:

```text
examples/golden/error-bar/
examples/golden/scatter-plot/
examples/golden/confidence-band/
examples/golden/groupplot/
```

Tests validate each FigureSpec, compare regenerated TeX byte-for-byte with the
committed snapshot, and compile a fresh PDF in a temporary directory.
