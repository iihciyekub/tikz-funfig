# Structured Petri nets

The `petri-net` Recipe draws an explicitly supplied place/transition net with
an initial marking and weighted directed arcs. It uses FigureSpec 1.1 and the
PGF/TikZ `petri` library. Start with:

```bash
PYTHONPATH=src python3 -m funfig init my-net --id my-net --recipe petri-net
PYTHONPATH=src python3 -m funfig validate my-net/figure.funfig.json
PYTHONPATH=src python3 -m funfig build my-net/figure.funfig.json
PYTHONPATH=src python3 -m funfig inspect my-net/figure.funfig.json
```

`petri.places` require `id`, `label`, `position: {x, y}`, and `tokens >= 0`.
`petri.transitions` require `id`, `label`, and `position`. Positions are in
centimeters. `petri.arcs` require `from`, `to`, and `weight >= 1`; optional
`bend` is in degrees from -80 to 80. A directed arc must connect one place
and one transition. Use one weighted arc instead of duplicate arcs between the
same endpoints. For opposing arcs, supply bends and inspect arrowheads/labels.

Plain labels are TeX-escaped. Set `label_format: "tex"` only for intentional
TeX math. Counts 0–9 use PGF's drawn token dots; counts of 10 or more appear as
numbers inside places because PGF's `tokens` style does not correctly handle
ten or more. The Recipe validates the static net contract; it does not infer
missing arcs or analyze reachability, liveness, or boundedness.

The independently authored [resource-loop golden](../../examples/golden/petri-resource-loop/figure.funfig.json)
shows a reversible resource arc with weight two. It compiles in the regression
suite and has been visually checked at the `journal-single-column` target width.
