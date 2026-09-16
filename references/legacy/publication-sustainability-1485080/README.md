# Sustainability 1485080 legacy figure sources

Historical publication figure material preserved as provenance for
TIKZ-FunFig.

| item | note |
| --- | --- |
| Journal | Sustainability (ISSN 2071-1050) |
| Manuscript ID | sustainability-1485080 |
| Type | Article |
| Title | NEVs Supply Chain Coordination with Financial Constraint and Demand Uncertainty |
| Figure set | fig1–fig11 |
| Original code author | Yongjian Li |
| Original date | 2021-01-12 |
| Original environment | Python 3.6.5, SymPy >= 1.3 |

## What is retained

Each figure directory keeps the lightweight material that is useful for
understanding or reproducing the historical workflow:

- the original `.tex` figure source;
- small scientific data files used by the plot;
- per-figure notes;
- `generate_data_legacy.py`, extracted from the original Jupyter notebook.

The extracted Python is provenance, not modern production code. Notebook-only
or syntactically incomplete cells are preserved as comments, and the code may
require the original package versions before it can execute unchanged.

## What was intentionally removed

Rendered PDF/SVG copies, Jupyter notebook containers/checkpoints, and other
generated state are not retained in this repository. They add repository noise
without adding source knowledge; the canonical visual regression cases now
live under `examples/golden/` and are rebuilt by the current test suite.

The strongest promoted cases are:

- `examples/golden/fig1/`
- `examples/golden/fig4/`
- `examples/golden/fig11/`

Use this legacy directory to understand original intent and provenance. Add new
runtime behavior to FigureSpec/Recipes/Renderers rather than making the Plugin
depend on these files.