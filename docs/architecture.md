# Architecture

## Why this is not just a template collection

TIKZ-FunFig separates declarative intent from generated TeX. A user edits a `FigureSpec`; a recipe interprets it; a renderer generates deterministic source; the build layer produces the PDF and manifest.

Between FigureSpec and rendering, the **Method layer** captures reusable semantic primitives
distilled from proven legacy helpers: implicit contours, curve probes, curve-relative labels,
coordinate formatting/templates, single or multiple named intersections, fill-between regions,
and spy/detail lenses. Methods preserve the behavior of the old macros without making new
figures depend on those macro files.

The migration layer is intentionally asymmetric: portable legacy idioms are promoted into
these methods, while ambiguous gnuplot programs or TeX-macro-dependent scripts remain explicit
warnings. Migration is therefore a semantic extraction pass, not a claim to be a complete TeX
parser.

This makes small later changes — a range, a color, an annotation, a series, a panel — local edits to structured data rather than full rewrites of hand-generated TikZ.

## Pipeline

```text
FigureSpec JSON
     │
     ├── schema validation
     │
     ├── recipe resolution
     │
     ├── data binding
     │
     ├── deterministic renderer
     │       └── figure.tex
     │
     ├── dependency detection
     │       ├── latexmk
     │       ├── pdflatex / xelatex
     │       └── gnuplot when requested
     │
     ├── build in .funfig/build/
     │       └── figure.pdf
     │
     └── manifest.json
```

## FigureSpec

The canonical machine-readable contract is `schemas/figure-spec.schema.json`. Version 1 uses JSON as the required interchange format so the core has no Python package dependency. YAML can be added later as an optional authoring surface without changing the schema semantics.

The stable top-level fields are:

- `schema_version`
- `id`
- `recipe`
- `kind`
- `canvas`
- `engine`
- `axes`
- `data_sources`
- `series`
- `regions`
- `annotations`
- `panels`
- `diagram`
- `outputs`

Recipes may require only a subset of these.

## Recipes

A recipe is metadata plus a renderer family and capability contract. Recipe files live in `recipes/` and are registered in `recipes/index.json`.

Core recipe families include:

1. `implicit-function` — managed gnuplot contours for implicit equations.
2. `function-plot` / `data-series` — analytic and data-driven 2D series.
3. `error-bar` / `scatter-plot` / `confidence-band` — scientific uncertainty and metadata plots.
4. `surface-plot` / `contour-plot` / `heatmap` / `quiver-field` — advanced field/3D views.
5. `threshold-region` / `intersection-curves` / `publication-threshold` — semantic regions, intersections, and publication callouts.
6. `groupplot` — aligned multi-panel PGFPlots.
7. `mechanism-diagram` — TikZ nodes and directed edges.

Recipes point back to local legacy examples so design knowledge can be promoted gradually instead of copied blindly.

## Artifact contract

For an input spec `figure.funfig.json`, defaults are:

- generated source: `figure.tex`
- canonical output: `figure.pdf`
- optional derived vector output: `figure.svg`
- build state: `.funfig/build/`
- manifest: `.funfig/manifest.json`

The `outputs.basename` field changes the stable generated names together.
`outputs.formats` defaults to `["pdf"]`; `["pdf", "svg"]` additionally derives
SVG from the successful PDF using `pdftocairo`.

## Manifest

`manifest.json` records:

- FigureSpec and recipe versions;
- renderer and tool dependencies;
- whether shell escape is required;
- source/output paths;
- SHA-256 of the FigureSpec and generated TeX;
- build status and timestamp;
- transient artifact policy.

The manifest is machine state, but it is intentionally human-readable.

## Cleanup

`funfig clean` removes only `.funfig/build/` and recognized transient PGFPlots/LaTeX files. It never removes the FigureSpec, user data, generated `.tex`, final `.pdf`, or requested `.svg`.

## Distribution

`packages/skill/` is the source package for the ChatGPT/Codex-style Skill. `scripts/sync_workspace_skill.sh` installs/synchronizes it into the workspace-local `.agents/skills/TIKZ-FunFig` target.

Future system Plugin packaging should consume the same schemas and recipe registry rather than reimplementing them.

