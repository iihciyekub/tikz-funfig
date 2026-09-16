# Architecture

## Why this is not just a template collection

TIKZ-FunFig separates declarative intent from generated TeX. A user edits a `FigureSpec`; a recipe interprets it; a renderer generates deterministic source; the build layer produces the PDF and manifest.

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

Initial recipes:

1. `function-plot` — analytic 2D functions.
2. `data-series` — file/coordinate driven scientific series.
3. `threshold-region` — curves plus highlighted intervals/rectangles.
4. `intersection-curves` — named curves and semantic intersections.
5. `groupplot` — aligned multi-panel PGFPlots.
6. `mechanism-diagram` — TikZ nodes and directed edges.

Recipes point back to local legacy examples so design knowledge can be promoted gradually instead of copied blindly.

## Artifact contract

For an input spec `figure.funfig.json`, defaults are:

- generated source: `figure.tex`
- final output: `figure.pdf`
- build state: `.funfig/build/`
- manifest: `.funfig/manifest.json`

The `outputs.basename` field changes both stable generated names together.

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

`funfig clean` removes only `.funfig/build/` and recognized transient PGFPlots/LaTeX files. It never removes the FigureSpec, user data, generated `.tex`, or final `.pdf`.

## Distribution

`packages/skill/` is the source package for the ChatGPT/Codex-style Skill. `scripts/sync_workspace_skill.sh` installs/synchronizes it into the workspace-local `.agents/skills/TIKZ-FunFig` target.

Future system Plugin packaging should consume the same schemas and recipe registry rather than reimplementing them.

