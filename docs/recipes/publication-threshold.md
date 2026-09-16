# publication-threshold recipe

`publication-threshold` is the first recipe distilled directly from the mature publication figures in:

- `sustainability-1485080-data-main/fig1/fig1.tex`
- `sustainability-1485080-data-main/fig4/fig4.tex`
- `sustainability-1485080-data-main/fig11/fig11.tex`

It captures the repeated semantic structure rather than copying one figure's hard-coded coordinates.

## Intended structure

Use this recipe for figures that combine most of the following:

- model parameters or scenario information in the axis title;
- semantically selected threshold ticks;
- primary and secondary/piecewise curves;
- highlighted rectangular regimes or fill-between regions;
- named paths and curve intersections;
- highlighted key points;
- arrow callouts with mathematical labels;
- a compact publication legend.

## Structured FigureSpec fields

The recipe uses standard `data_sources`, `series`, `regions`, and `annotations`, plus publication-oriented axis fields such as `title`, `axis_line_shift`, `tick_precision`, and structured `legend` settings.

Point and intersection annotations can bind marker styling, a label, relative shift, font, and an arrow to the same semantic point. This keeps the relationship stable when the underlying curve data changes.

## Legacy migration

For an existing PGFPlots source, start with:

```bash
funfig migrate-legacy old-figure.tex new-figure/
```

The migration is intentionally conservative. It currently recognizes common local patterns for numeric axis bounds/ticks, table and coordinate plots, `name path` bindings, and rectangular regions.

Complex manual nodes, macro-generated labels, legends, and intersection callouts are reported as migration warnings and must be reviewed. The resulting `metadata.migration.status` remains `draft` until that review is complete.

## Golden publication cases

The recipe is regression-tested against three real figures:

- `examples/golden/fig1` — threshold region, inverse-CDF curve, piecewise order-quantity curves, and five semantic point annotations;
- `examples/golden/fig4` — two profit series, two highlighted increasing regions, named-path intersection, and arrow callouts;
- `examples/golden/fig11` — paired piecewise contract curves and five threshold-point callouts.

These are not migration drafts. They are manually reviewed FigureSpecs whose
generated TeX is committed as a golden snapshot. When renderer behavior changes
intentionally, visually inspect the rebuilt PDFs first, then update the golden
TeX snapshots together with the renderer change.
