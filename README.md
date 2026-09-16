# TIKZ-FunFig

TIKZ-FunFig is a schema-driven figure generation system for reproducible TikZ and PGFPlots figures.

The repository has two roles:

1. **Source project** — schemas, recipes, renderers, tests, documentation, and packaging live here.
2. **Knowledge base** — the existing TikZ/PGFPlots notes and publication examples remain available as local references and are gradually promoted into stable recipes.

The repository is the source of truth. Workspace/system Skills or future Plugins are installation targets generated or synchronized from this project; they should not become independent forks.

## Stable figure contract

A generated figure project uses this layout:

```text
my-figure/
├── figure.funfig.json      # editable FigureSpec; source of truth
├── figure.tex              # deterministic generated source
├── figure.pdf              # stable compiled artifact
├── data/                   # optional user/source data
└── .funfig/
    ├── manifest.json       # recipe, dependencies, outputs, hashes/status
    └── build/              # disposable compiler/intermediate files
```

Only `figure.funfig.json`, explicit source data, generated `figure.tex`, and the final PDF are user-facing artifacts. LaTeX/PGFPlots temporary files belong under `.funfig/build/` and may be removed safely.

## CLI

No third-party Python dependency is required for the v0.1 core.

```bash
PYTHONPATH=src python3 -m funfig recipes
PYTHONPATH=src python3 -m funfig validate examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig render examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig build examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig clean examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig migrate-legacy path/to/legacy.tex path/to/new-figure
```

For publication figures with thresholds, piecewise curves, highlighted regimes, intersections, and arrow callouts, use the `publication-threshold` recipe. It is distilled from the mature `fig1`, `fig4`, and `fig11` examples in the local knowledge base.

For a local editable command:

```bash
python3 -m pip install -e .
funfig recipes
```

## Architecture

The main concepts are intentionally separate:

- **FigureSpec Schema** — what the requested figure contains.
- **Figure Recipe** — how a class of figures is interpreted and which renderer/tools it uses.
- **Renderer** — deterministic conversion from FigureSpec to TikZ/PGFPlots source.
- **Data Binding** — mapping from named data sources to series/panels/annotations.
- **Artifact Contract** — stable file names and output layout.
- **Manifest** — record of recipe, dependencies, source/output files, and build status.
- **Cleanup Policy** — which intermediate files are disposable.

See `docs/architecture.md` for details.

See `docs/recipes/publication-threshold.md` for the first publication-derived recipe and the conservative legacy migration workflow.

## Legacy/local knowledge

The existing directories are intentionally preserved:

- `TikZ_memo_v_0_6_0623/`
- `pgfplots_memo_v0_0_0_1/`
- `sustainability-1485080-data-main/`

They are reference material. New stable behavior should be implemented in `schemas/`, `recipes/`, `src/`, and `packages/skill/`, then validated with tests.

