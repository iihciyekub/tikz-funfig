# Contributing to TIKZ-FunFig

TIKZ-FunFig treats FigureSpec, recipes, renderers, golden figures, and the portable Codex Plugin as one compatibility surface. Changes should preserve reproducibility rather than only making one example compile.

## Before editing

Read `AGENTS.md`, `docs/DEVELOPMENT.md`, and `docs/GIT_WORKFLOW.md`. For schema or renderer work, also read `docs/architecture.md` and the nearest recipe documentation.

## Development checklist

1. Work from a clean `main` or a focused branch.
2. Change canonical source files, not generated Plugin copies.
3. Add/update a golden case when observable TeX output changes intentionally.
4. Add/update regression coverage for bug fixes and new behavior.
5. Run:

   ```bash
   ./scripts/sync_plugin_package.sh
   ./scripts/check.sh
   git diff --check
   ```

6. Review `git diff` before committing.
7. Keep each commit limited to one logical concern.

## Pull requests

PRs should explain the user-visible behavior, the contract impact, tests/golden cases changed, and whether the change is backward compatible. CI must pass before merge.

Do not include generated PDFs, build caches, `.funfig` runtime state, local fonts, notebook state, or unrelated cleanup.

## Releases

Do not manually edit published tags or the installed Codex cache. Follow `docs/RELEASE.md`; releases are created through `./scripts/release.sh X.Y.Z`.

