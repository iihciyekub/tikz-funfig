# TIKZ-FunFig

TIKZ-FunFig is a schema-driven figure generation system for reproducible TikZ and PGFPlots figures.

Version 0.9.0 expands TIKZ-FunFig into a multi-Skill academic-figure Plugin with
FigureSpec 1.1 structured diagrams, searchable PGF/TikZ knowledge, Publication
Profiles, themes, visual QA, and a sourced Expert TikZ fallback for long-tail
manual-backed features. Existing 1.0 managed figures and the promoted PGFPlots/
legacy migration paths remain supported.

The repository has three roles:

1. **Source project** — schemas, recipes, renderers, tests, documentation, and packaging live here.
2. **Knowledge base** — compiled task cards and a section-level PGF/TikZ 3.1.11a corpus are directly searchable by the Plugin.
3. **Provenance source tree** — pinned official/community material lives under `sources/`; legacy project material remains under `references/`. Neither is a Plugin runtime dependency.

The repository is the source of truth. Workspace/system Skills and the portable Codex/OpenAI Plugin are installation targets generated or synchronized from this project; they should not become independent forks.

## Stable figure contract

A generated figure project uses this layout:

```text
my-figure/
├── figure.funfig.json      # editable FigureSpec; source of truth
├── figure.tex              # deterministic generated source
├── figure.pdf              # canonical compiled artifact
├── figure.svg              # optional derived vector artifact
├── data/                   # optional user/source data
└── .funfig/
    ├── manifest.json       # recipe, dependencies, outputs, hashes/status
    └── build/              # disposable compiler/intermediate files
```

`figure.funfig.json`, explicit source data, generated `figure.tex`, the final PDF, and any requested SVG are user-facing artifacts. LaTeX/PGFPlots temporary files belong under `.funfig/build/` and may be removed safely.

Figure directories belong to the active user project, not to the installed
Plugin cache. An explicit requested directory takes precedence. Without one,
new figures use `<project-root>/figures/<figure-id>/`; existing managed figures
are revised in place. `funfig init --id <id>` uses the current project working
directory by default; `--project-root` or `FUNFIG_PROJECT_ROOT` can override it.
PDF is canonical; set `outputs.formats` to `["pdf", "svg"]` to derive SVG.

## CLI

No third-party Python dependency is required for the v0.1 core.

```bash
PYTHONPATH=src python3 -m funfig recipes
PYTHONPATH=src python3 -m funfig capabilities
PYTHONPATH=src python3 -m funfig kb search "relative positioning"
PYTHONPATH=src python3 -m funfig templates list
PYTHONPATH=src python3 -m funfig templates search "research framework"
PYTHONPATH=src python3 -m funfig templates inspect layered-framework
PYTHONPATH=src python3 -m funfig themes
PYTHONPATH=src python3 -m funfig profiles
PYTHONPATH=src python3 -m funfig validate examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig render examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig build examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig inspect examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig clean examples/basic-function/figure.funfig.json
PYTHONPATH=src python3 -m funfig migrate-legacy path/to/legacy.tex path/to/new-figure
PYTHONPATH=src python3 -m funfig init --id fig1 --recipe publication-threshold
PYTHONPATH=src python3 -m funfig init --project-root path/to/paper --id fig1 --recipe publication-threshold
```

Repository maintainers rebuild the pinned PGF/TikZ source-example corpus with:

```bash
python3 scripts/build_source_example_corpus.py build
python3 scripts/build_source_example_corpus.py verify --compile-samples
```

Ordinary 2D paper/scientific recipes default to the `publication-offset` axes
preset (6.5pt axis-line shift), inward major ticks, thin publication strokes,
endpoint tick marks at both declared axis limits, and low-contrast translucent
annotation backing. Set `axes.preset` to
`standard` to opt out, or set `axes.axis_line_shift` to choose another offset.
Advanced 3D/contour/heatmap/quiver recipes retain the standard axes preset by default.

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
- **Knowledge layer** — compiled task cards plus normalized searchable manual/source-example corpora.
- **Template layer** — curated regression-backed FigureSpec/TeX starting points with explicit edit contracts.
- **Source layer** — pinned upstream/provenance material used to rebuild or verify normalized knowledge; never a runtime dependency.
- **Renderer** — deterministic conversion from FigureSpec to TikZ/PGFPlots source.
- **Theme** — appearance tokens that never change graph/data semantics.
- **Publication Profile** — target physical size and readability/QA constraints.
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
six Skills (general, plots, flowcharts, frameworks, relations, schematics), one
shared searchable knowledge tree, the bundled runtime, Schema/Recipe registry,
themes, Publication Profiles, and visual assets. The original `pgfmanual.pdf`
is not a runtime dependency. `IconKitchen/macos/AppIcon128.png` and `AppIcon512.png` are the canonical
composer icon/logo sources. Run `scripts/sync_plugin_package.sh` after changing
Skills, runtime, schemas, recipes, knowledge, themes/profiles, or icons.

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

With this repository available locally, one command installs both the `tff` CLI
and the Git-backed Codex Plugin:

```bash
./scripts/install_codex.sh
```

The CLI lives in `~/.local/bin` (Python 3 required). From any directory:

```bash
tff install
tff update
tff status
```

`tff upgrade` is an alias for `tff update`; `tff --version` shows the CLI version,
while `tff status` shows the installed Plugin version. Updates preserve the
configured Git ref and keep the existing installation if refreshing fails.
Use `./scripts/install_codex.sh --cli-only` to install just the CLI. The installer
fetches the configured Git source, not unpublished working-tree changes.
See [installation details](docs/INSTALL_UPDATE.md) for a fresh-machine command.

Useful companion commands include `tff doctor`. Repository
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

The confirmed official-manual knowledge base and multi-Skill implementation
contract is specified in [TFF-SPEC-001](docs/specs/multi-skill-knowledge-base-spec.md).
The Spec distinguishes currently implemented V1 work from later tree/state/ER/
advanced-layout phases and is the acceptance baseline for this development cycle.

The source-example corpus, template-library, repository-cleanup, and future
PGFPlots/community ingestion architecture is specified in
[TFF-SPEC-002](docs/specs/source-example-corpus-plugin-spec.md).

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

## External and legacy knowledge

Pinned official/upstream source material is isolated under `sources/`.
`sources/registry.json` records its version, license, local path, and Plugin
distribution policy. Raw upstream trees are development inputs only; normalized
search data belongs in `knowledge/`.

Historical source material is intentionally isolated from the runtime under `references/legacy/`:

- `references/legacy/tikz-memo/`
- `references/legacy/pgfplots-memo/`
- `references/legacy/publication-sustainability-1485080/`

They are development reference material, not Plugin runtime dependencies. Rendered binaries, font copies, notebook containers/checkpoints, and build state are intentionally excluded. Historical notebook computation cells are preserved as plain `generate_data_legacy.py` sources where relevant.

See `references/README.md` for the promotion/retention policy. New stable behavior should be implemented coherently in `knowledge/`, `schemas/`, `recipes/`, `themes/`/`profiles/` when relevant, `src/`, and canonical Skills, then validated with golden cases and tests.
