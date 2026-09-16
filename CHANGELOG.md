# Changelog

All notable changes to TIKZ-FunFig are recorded here. The project follows semantic versioning while the FigureSpec/Plugin contract is still pre-1.0.

## [Unreleased]

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

