# Changelog

All notable changes to TIKZ-FunFig are recorded here. The project follows semantic versioning while the FigureSpec/Plugin contract is still pre-1.0.

## [Unreleased]

## [0.11.0] - 2026-09-24

### Added

- Added the additive `figure.design.json` schema and `validate-design` command
  for user intent, image-reference roles, layout/typography targets, and stable
  structured/Expert delivery. Final delivery checks verify artifacts, current
  build hashes, and recorded machine/visual QA.

### Changed

- Refactored all six Skills around context-driven family routing and shared
  request interpretation, image references, focused knowledge queries,
  composition, sourced Expert TikZ, final-size review, and output contracts.
- Expanded the curated composition layer from 10 to 13 templates with
  regression-backed feedback-loop, merge/split, and grouped-framework layouts,
  plus searchable design-fit metadata and end-to-end Skill design fixtures.
- Made implicit invocation explicit in Skill metadata and preserved the existing
  FigureSpec compatibility and single shared knowledge/runtime distribution.
- Clarified that enlarging a canvas does not solve readability at a fixed final
  width and that design records do not imply automatic aesthetic verification.

## [0.10.0] - 2026-09-24

### Added

- Added a runtime-enforced project output contract: explicit destinations win,
  existing managed figures stay in place, and new figures default to
  `<active-project>/figures/<figure-id>/` via `--project-root`,
  `FUNFIG_PROJECT_ROOT`, or the current project working directory.
- Added `outputs.formats` with canonical PDF plus optional SVG export through
  Poppler `pdftocairo`, including manifest hashes and dependency checks.
- Added pinned PGF/TikZ and PGFPlots source-example corpora, direct PGFPlots
  manual-section indexing from the official TeX include tree, and curated
  community source knowledge with provenance/license metadata.
- Added curated paper-grade Templates for frameworks, flowcharts, relations,
  schematics, confidence bands, error bars, metadata scatter, grouped panels,
  heatmaps, and 3D surfaces.
- Added final-size Publication Profile QA metrics and portable Plugin bundle
  hygiene/standalone-install regression.
- Added centralized version management with `pyproject.toml` as the canonical
  version source plus checked runtime/helper/Plugin synchronization.

### Changed

- Plot Recipes now bind to curated PGFPlots knowledge cards instead of
  production dependencies on legacy reference paths.
- Knowledge search now combines Recipes, Templates, curated cards, official
  examples, official manual sections, and community examples with
  production-oriented ranking and exact-title preference.
- Codex Plugin documentation now separates local checkout installation,
  private Git marketplace distribution, release-tag installs, workspace
  publishing, and universal public Plugin submission.

## [0.9.0] - 2026-09-22

### Added

- Added five specialized Skills (`funfig-plots`, `funfig-flowcharts`,
  `funfig-frameworks`, `funfig-relations`, and `funfig-schematics`) alongside
  the compatibility/general `TIKZ-FunFig` entry, all sharing one runtime and knowledge layer.
- Added the verified PGF/TikZ 3.1.11a manual pipeline: pinned source manifest,
  complete split plan, topic map, section-level searchable corpus, 24 compiled
  knowledge cards, and executable knowledge examples.
- Added SQLite FTS5/BM25 knowledge search (`funfig kb`), capability discovery,
  four structured diagram Recipes, FigureSpec 1.1, four themes, and three
  Publication Profiles.
- Added explicit post-build inspection/visual-QA state and sourced Expert TikZ
  Mode for long-tail manual-backed capabilities outside stable FigureSpec coverage.

### Changed

- Portable Plugin packaging now distributes six Skills, shared lightweight
  knowledge, themes, and Publication Profiles while keeping original/split PDFs
  and legacy provenance outside the runtime package.
- Structured diagram generation now validates layout/group cycles, node/edge
  references, route-specific parameters, grid collisions, role/shape semantics,
  plain-text escaping, grouping, and deterministic library resolution before TeX compilation.

## [0.8.5] - 2026-09-22

### Changed

- Improved the standalone `tff` installer/updater with an `upgrade` alias,
  CLI version reporting, actual installed-version lookup, and optional dependency checks.
- Marketplace refresh failures now stop without uninstalling the existing Plugin;
  configured Git refs are preserved during ordinary updates.
- Added helper-only setup and bundled the helper so successful Plugin updates can
  refresh the installed CLI. Repository update scripts use the current helper.
- Documented quick installation, update behavior, and the proposed multi-Skill
  architecture. The multi-Skill expansion remains a specification, not a shipped capability.

### Fixed

- Improved publication callout readability with a 0.94-opacity white backing,
  separate point/intersection label styling, and connectors that honor explicit
  label anchors. Updated and visually checked publication golden cases.

## [0.8.4] - 2026-09-17

### Changed

- Refined `publication-offset` with inward major ticks while preserving thin
  publication strokes and endpoint tick alignment.
- Added subtle translucent white backing to publication annotation/callout text.
- Increased starter canvas dimensions slightly for ordinary 2D publication recipes.
- Updated the figure style guide to prefer larger canvases for text-heavy multi-panel figures.

## [0.8.3] - 2026-09-17

### Added

- Repository governance documentation for development, Git workflow, releases, Codex installation/update/rollback, and Plugin distribution.
- Root `AGENTS.md`, contribution guidance, pull-request template, and GitHub CI workflow.

### Changed

- Release automation now requires a matching changelog section before publishing.

## [0.8.2] - 2026-09-17

### Changed

- Moved Codex distribution to the canonical Git-backed `tikz-funfig` marketplace.
- Added one-command `tff update`, install/status/doctor helpers, repository cleanup, and release automation.

### Fixed

- Removed the historical local marketplace registration during migration to the GitHub marketplace.

## [0.8.0] - 2026-09-17

### Added

- Promoted legacy TikZ/PGFPlots methods into structured FigureSpec capabilities, including implicit gnuplot contours, curve probes/labels, multi-intersections, coordinate templates, spy annotations, and legacy-method migration.

## [0.7.0] - 2026-09-17

### Added

- Structured method layer for legacy `\iiplot`, coordinate extraction, curve-relative annotations, intersections, and fill-between semantics.

## [0.6.0] - 2026-09-17

### Added

- `publication-offset` as the default two-dimensional publication axis preset.
- Project output policy for predictable `figures/<figure-id>/` placement.
