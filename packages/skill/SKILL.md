---
name: TIKZ-FunFig
description: Create, revise, and validate publication-quality scientific figures with TikZ and PGFPlots, using the workspace's tikz-funfig knowledge base as the primary local reference.
---

# TIKZ-FunFig

Use this skill when the user asks to create, reproduce, beautify, repair, or convert a scientific/academic figure using TikZ, PGFPlots, or LaTeX-native vector graphics.

The primary local knowledge base is:

`tikz-funfig/`

Treat that directory as **reference material**. Do not modify it unless the user explicitly asks. Create new figure sources in the user's active paper/draft directory.

## Core goals

1. Treat `figure.funfig.json` (FigureSpec) as the editable source of truth for generated figures.
2. Produce clean, deterministic `.tex` source rather than a raster-only result.
3. Prefer a standalone, reproducible figure that compiles independently.
4. Match the visual grammar already demonstrated in `tikz-funfig/`: restrained grids, clear mathematical labels, highlighted regimes/regions, compact callouts, vector annotations, and data-driven PGFPlots where appropriate.
5. Validate the FigureSpec and compile the generated source locally when the toolchain is available.
6. Keep figure code maintainable: data binding, visual semantics, generated source, build state, and final artifacts must have stable responsibilities.

## Schema-first contract

For a new figure or a figure already managed by TIKZ-FunFig, **do not start by freely rewriting `figure.tex`**. Use the Figure Recipe System in the `tikz-funfig` project:

```text
FigureSpec -> Recipe -> Data Binding -> Renderer -> figure.tex -> Build -> figure.pdf
                                                    \-> manifest.json
```

The canonical authoring file is:

`figure.funfig.json`

The stable figure directory contract is:

```text
figure-directory/
├── figure.funfig.json
├── figure.tex
├── figure.pdf
├── data/                  # optional source data
└── .funfig/
    ├── manifest.json
    └── build/             # disposable intermediates; normally cleaned after success
```

For supported properties — axis ranges, labels, styles, data bindings, series, regions, annotations, panels, nodes, edges — update the FigureSpec and regenerate. Do not patch generated TeX as the long-term source of truth.

If the requested behavior is not expressible by the current schema/recipe, it is acceptable to extend the project schema/recipe/renderer first. Avoid one-off generator logic when the capability is reusable.

Read `references/schema-contract.md` for the field and artifact responsibilities.

### Core commands

The installed Skill includes a wrapper that calls the source project:

```bash
.agents/skills/TIKZ-FunFig/scripts/funfig.sh recipes
.agents/skills/TIKZ-FunFig/scripts/funfig.sh validate path/to/figure.funfig.json
.agents/skills/TIKZ-FunFig/scripts/funfig.sh render path/to/figure.funfig.json
.agents/skills/TIKZ-FunFig/scripts/funfig.sh build path/to/figure.funfig.json
.agents/skills/TIKZ-FunFig/scripts/funfig.sh clean path/to/figure.funfig.json
```

To initialize a new figure:

```bash
.agents/skills/TIKZ-FunFig/scripts/funfig.sh init path/to/new-figure --recipe function-plot
```

Initial stable recipes are:

- `function-plot`
- `data-series`
- `threshold-region`
- `intersection-curves`
- `groupplot`
- `mechanism-diagram`

## Required toolchain

For the full TIKZ-FunFig workflow, treat the following as required local dependencies:

- a TeX distribution with `pdflatex` and `xelatex`;
- `latexmk`;
- `gnuplot` for PGFPlots `gnuplot` / `raw gnuplot` plots, especially implicit-function figures.

On macOS, the supported setup path is Homebrew. Run:

```bash
.agents/skills/TIKZ-FunFig/scripts/setup_macos.sh
```

or install gnuplot directly with:

```bash
brew install gnuplot
```

Verify the environment with:

```bash
.agents/skills/TIKZ-FunFig/scripts/check_dependencies.sh
```

Read `references/dependencies.md` for details, including the `-shell-escape` requirement for TeX-to-gnuplot execution.

## Workflow

### 1. Classify the requested figure and choose a recipe

Choose the simplest suitable mode:

- **TikZ diagram** — `mechanism-diagram` for conceptual models, workflows, mechanisms, arrows, and named nodes.
- **PGFPlots analytic plot** — `function-plot` for explicit or gnuplot-backed functions.
- **PGFPlots data plot** — `data-series` for CSV/DAT/table/coordinate-driven figures.
- **Threshold/regime plot** — `threshold-region` for shaded regimes, threshold bands, and callouts.
- **Curve intersection plot** — `intersection-curves` for named paths and semantic intersections.
- **Multi-panel** — `groupplot` when panels should share a coherent figure system.

Read `references/reference-map.md` before searching the knowledge base broadly.

### 2. Inspect the nearest local examples

Use the reference map to read only the most relevant `.tex` examples. Reuse ideas and idioms, not accidental hard-coded coordinates or obsolete compatibility settings.

When an existing figure in the user's paper is being revised, inspect that source first and preserve its semantic variables, labels, and data interfaces unless asked to redesign them.

### 3. Create/update FigureSpec, then generate standalone source

Define the semantic structure and data binding in `figure.funfig.json`, validate it, and render the `.tex`. For a managed figure, generated TeX is an artifact of the spec.

When extending a renderer/template, the default generated skeleton remains:

Default skeleton:

```tex
\documentclass[border=2pt]{standalone}
\usepackage[dvipsnames,svgnames,x11names]{xcolor}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
```

Load only the libraries required by the figure. Common local patterns use:

```tex
\usetikzlibrary{calc,arrows.meta,positioning,intersections}
\usepgfplotslibrary{fillbetween,groupplots}
```

For Chinese text, prefer XeLaTeX and a font available on the current machine. Do not copy or redistribute font files from the reference directory.

### 4. Apply publication-oriented defaults

Follow `references/style-guide.md`.

In particular:

- use vector geometry and text;
- avoid decorative effects that do not communicate information;
- keep line weights, marker sizes, and fonts consistent;
- avoid overcrowded legends and callouts;
- use opacity sparingly for regime fills;
- keep annotations inside or near the plot without covering primary data;
- use named coordinates/paths rather than repeated magic coordinates when possible;
- use `name path` + `intersections` or `fill between` when the semantic structure warrants it;
- when data already exists in a file, plot it directly instead of copying values into source code.

### 5. Data and reproducibility

Prefer these patterns, in order:

1. `\addplot table[...] {data-file};` for existing tabular data.
2. `coordinates {...}` for small fixed point sets.
3. analytic `\addplot {expression};` for explicit functions.
4. Python-generated data only when the mathematical transformation is cumbersome in PGF/TikZ or the source workflow already uses Python.

Keep generated data beside the figure or in a clearly named `data/` directory. Do not silently overwrite scientific source data.

### 6. Compile and repair

For schema-managed figures, use:

```bash
.agents/skills/TIKZ-FunFig/scripts/funfig.sh build path/to/figure.funfig.json
```

For a standalone legacy `.tex` that has not yet been converted to FigureSpec, the lower-level compiler remains available:

```bash
.agents/skills/TIKZ-FunFig/scripts/compile_tikz.sh path/to/figure.tex
```

It selects XeLaTeX when the source declares it or uses CJK packages; otherwise it uses pdfLaTeX through `latexmk`. If the source uses PGFPlots `gnuplot`/`raw gnuplot`, the script also verifies that `gnuplot` is installed and enables TeX shell escape for that compile.

If compilation fails:

1. read the first meaningful TeX error rather than only the last line;
2. fix missing packages/libraries, malformed coordinates, data paths, or math syntax;
3. compile again;
4. stop only after the source builds or after clearly identifying an unavailable external dependency.

### 7. gnuplot-backed figures

The local knowledge base contains an `\iiplot` macro that uses PGFPlots `raw gnuplot` for implicit functions. gnuplot is therefore part of the full skill toolchain rather than an optional afterthought.

When a source uses `gnuplot` or `raw gnuplot`:

- require `gnuplot` to be available on `PATH`;
- compile through the bundled script so `-shell-escape` is enabled only when needed;
- use `raw gnuplot` for genuine implicit/contour problems where it is the clearest approach;
- prefer direct PGFPlots expressions for ordinary explicit functions where an external process adds no value;
- never enable shell escape for arbitrary uninspected third-party TeX source. Inspect the source first because shell escape allows TeX to launch external commands.

## Supported tasks

- create a figure from a textual specification;
- reproduce a supplied plot/diagram in TikZ/PGFPlots;
- convert an existing Python/Matplotlib-style scientific plot into LaTeX-native vector source;
- redesign an existing `.tex` figure while preserving data/meaning;
- combine several plots into a coherent multi-panel figure;
- add annotations, intersection labels, highlighted regions, arrows, legends, error bars, or data labels;
- diagnose and fix TikZ/PGFPlots compilation failures;
- extract repeated styles/macros from several figures into reusable definitions.

## Output contract

For a normal figure-generation task, produce:

1. `figure.funfig.json` — canonical structured specification;
2. the generated `.tex` figure source;
3. any explicit local source data file(s) required by the figure;
4. `.funfig/manifest.json` — recipe/dependency/hash/build record;
5. a successful compile result when the toolchain supports it;
6. the generated PDF;
7. no stray LaTeX/gnuplot intermediates in the user-facing figure directory after a successful default build.

Do not claim successful compilation unless it was actually run successfully.

## Local knowledge base rules

- `tikz-funfig/TikZ_memo_v_0_6_0623/` contains TikZ/PGFPlots/LaTeX technique notes and examples.
- `tikz-funfig/pgfplots_memo_v0_0_0_1/` contains compact PGFPlots examples and parameter experiments.
- `tikz-funfig/sustainability-1485080-data-main/` contains publication-style figures with `.tex`, `.pdf`, `.svg`, data files, and Python notebooks.
- Prefer `compat=1.18` for newly created PGFPlots sources unless an existing paper requires another compatibility level.
- Some old notes are exploratory snippets rather than canonical best practice. Validate syntax before reusing it.

For detailed locations, see `references/reference-map.md`.

## Project/distribution rule

The `tikz-funfig/` Git repository is the source of truth for schemas, recipes, renderers, tests, and the packaged Skill. Do not make permanent feature changes only inside `.agents/skills/TIKZ-FunFig`; make them in the project and synchronize the packaged Skill from there.

