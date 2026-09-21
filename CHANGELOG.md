# Changelog

All notable changes to TIKZ-FunFig are recorded here. The project follows semantic versioning while the FigureSpec/Plugin contract is still pre-1.0.

## [Unreleased]

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
