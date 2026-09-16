# TIKZ-FunFig

TIKZ-FunFig is a schema-driven figure generation system for reproducible TikZ and PGFPlots figures.

Version 0.8.3 extends the promoted method layer and the legacy migration path. Implicit equations
no longer require hand-written `raw gnuplot`; curve-relative probes/labels replace the old
`\addpoint` / `\addsymbol` pattern; named intersections can preserve multiple crossings;
coordinate templates embed live x/y values in publication labels; and TikZ spy/detail lenses
are represented as structured annotations. `migrate-legacy` now recognizes common
`\iiplot` / `\iipolt`, simple intersection, `\calxy`, `\addpoint`, and `\addsymbol` idioms.

The repository has two roles:

1. **Source project** — schemas, recipes, renderers, tests, documentation, and packaging live here.
2. **Knowledge base** — the existing TikZ/PGFPlots notes and publication examples remain available as local references and are gradually promoted into stable recipes.

The repository is the source of truth. Workspace/system Skills and the portable Codex/OpenAI Plugin are installation targets generated or synchronized from this project; they should not become independent forks.

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

Figure directories belong to the active user project, not to the installed
Plugin cache. An explicit requested directory takes precedence. Without one,
new figures use `<project-root>/figures/<figure-id>/`; existing managed figures
are revised in place.

## CLI

No third-party Python dependency is required for the v0.1 core.

```bash
PYTHONPATH=src python3 -m funfig recipes
PYTHONPATH=src python3 -m funfig validate examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig render examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig build examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig clean examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig migrate-legacy path/to/legacy.tex path/to/new-figure
PYTHONPATH=src python3 -m funfig init --project-root path/to/paper --id fig1 --recipe publication-threshold
```

Ordinary 2D paper/scientific recipes default to the `publication-offset` axes
preset (6.5pt axis-line shift). Set `axes.preset` to `standard` to opt out, or
set `axes.axis_line_shift` to choose another offset. Advanced 3D/contour/
heatmap/quiver recipes retain the standard axes preset by default.

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

See `docs/recipes/scientific-series.md` for the structured error-bar, scatter,
confidence-band, and groupplot family. Golden examples for all four live under
`examples/golden/` and are compiled in the regression suite.

See `docs/recipes/advanced-plots.md` for the structured surface, contour,
heatmap, and quiver family. Contour generation uses the managed gnuplot path;
the other three remain pure PGFPlots/TeX.

## Portable Plugin

`packages/plugin/tikz-funfig/` is a portable Agent Plugins package containing
the TIKZ-FunFig Skill, bundled runtime, Schema/Recipe registry, and visual
assets. `IconKitchen/macos/AppIcon128.png` and `AppIcon512.png` are the canonical
composer icon/logo sources. Run `scripts/sync_plugin_package.sh` after changing
the Skill, runtime, schemas, recipes, or icons.

The repo-local Codex marketplace manifest is `.agents/plugins/marketplace.json`.

## GitHub / Codex installation

The canonical Codex marketplace name is `tikz-funfig`. The Git source is the
private repository `git@github.com:iihciyekub/tikz-funfig.git`; a machine must
therefore have GitHub SSH access before installing it.

Native Codex installation does not require cloning the repository:

```bash
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref main \
  && codex plugin add tikz-funfig@tikz-funfig
```

When this repository is available locally, `scripts/install_codex.sh` also
installs the small `tff` helper into `~/.local/bin`. After that the normal
update workflow is simply:

```bash
tff update
```

Useful companion commands are `tff status` and `tff doctor`. Repository
maintainers can remove reproducible local build/noise files with
`scripts/clean_repo.sh`.

Releases use a clean working tree and one command:

```bash
./scripts/release.sh 0.9.0
```

The release command updates the package version, rebuilds the portable Plugin,
runs the full regression suite, creates the release commit and annotated Git
tag, pushes `main` and the tag, then refreshes the local Codex installation
when the Codex CLI is available.

## Development and governance

Repository rules are intentionally documented outside this README so future
contributors and coding agents do not depend on chat history:

- `AGENTS.md` — mandatory repository rules and source-of-truth map;
- `CONTRIBUTING.md` — contribution checklist;
- `docs/DEVELOPMENT.md` — development architecture and capability workflow;
- `docs/GIT_WORKFLOW.md` — commit, branch, and push rules;
- `docs/RELEASE.md` — semantic versioning and release procedure;
- `docs/INSTALL_UPDATE.md` — Codex install, update, status, and rollback;
- `docs/PLUGIN_DISTRIBUTION.md` — source → portable Plugin → Codex cache contract;
- `CHANGELOG.md` — release history and pending changes.

GitHub CI is defined in `.github/workflows/ci.yml` and runs the portable-bundle
consistency check plus the full TeX/gnuplot regression suite on pushes to
`main` and on pull requests.

## Publication golden cases

`examples/golden/fig1`, `fig4`, and `fig11` are schema-managed reconstructions
of three real publication figures from the local sustainability reference set.
Each case is self-contained: its FigureSpec binds to copied source data under
`data/`, records provenance back to the legacy source, and includes the
deterministic generated `.tex` as a regression snapshot.

Tests re-render each golden case in a temporary directory and compare the
generated TeX byte-for-byte with the committed snapshot. They also compile all
three figures with the local TeX toolchain. PDFs are verified as build outputs
but are not binary-hashed or committed because TeX/PDF metadata may vary by
toolchain version.

## Legacy/local knowledge

Historical source material is intentionally isolated from the runtime under `references/legacy/`:

- `references/legacy/tikz-memo/`
- `references/legacy/pgfplots-memo/`
- `references/legacy/publication-sustainability-1485080/`

They are development reference material, not Plugin runtime dependencies. Rendered binaries, font copies, notebook containers/checkpoints, and build state are intentionally excluded. Historical notebook computation cells are preserved as plain `generate_data_legacy.py` sources where relevant.

See `references/README.md` for the promotion/retention policy. New stable behavior should be implemented in `schemas/`, `recipes/`, `src/`, and `packages/skill/`, then validated with golden cases and tests.

