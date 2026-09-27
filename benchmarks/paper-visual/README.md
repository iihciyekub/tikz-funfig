# Paper-figure visual regression

`cases.json` defines five reproducible stress cases derived from curated
Templates: a CJK moderation model in one column, a long-label business
framework in two columns, a math relation model in one column, a confidence
band in one column, and a CJK feedback flowchart in two columns. These are
representative synthetic paper figures, not figures extracted from five real
papers. The language/profile matrix is deliberately small; passing it does not
establish coverage of every figure family or publisher style.

Run from the repository root with a temporary output directory:

```bash
PYTHONPATH=src python3 benchmarks/paper-visual/run_cases.py /tmp/tff-paper-visual
```

The runner builds and inspects all cases, writes their FigureSpecs, PDFs,
previews, manifests, and `machine-results.json` under the output directory,
and checks measured PDF width against each case's column budget. It does not
approve visual QA. View every preview at its intended size, inspect text,
arrows, H labels, axes, whitespace, and data meaning, then record a review with
`funfig qa` and summarize evidence. `results-2026-09-27.json` is the first
agent-reviewed result: **5/5 final previews passed**, including width and
machine checks. No independent human review or pixel similarity is claimed.

The first pass surfaced three actionable defects:

- The single-column confidence band used automatic scientific-notation ticks
  near zero; its tick labels overlapped and the full PDF was 90.9 mm wide for
  an 88 mm budget. Explicit y ticks and a smaller axes canvas yielded 78.8 mm.
- The CJK feedback arrow returned above the main path and crossed the figure.
  The canonical feedback Template now routes it below the main path.
- The business framework split “market” across two lines. Grid `auto_fit`
  nodes now suppress ordinary English word hyphenation. A very long unbroken
  word can still overflow, so the final preview remains necessary.

The moderation starter also placed H1 at the midpoint where the moderator
arrow arrives. Its label now sits earlier on the X-to-Y path. The structured
review history fix preserves failed QA rounds after a rebuild; the recorded
`repair_cycles` in the dated report are zero because those first-pass reviews
were observed before a CLI failure was recorded for this suite. The notes above
document the defects without inventing history.
