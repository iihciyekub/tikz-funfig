# TIKZ-FunFig Agent Rules

Read this file before modifying the repository.

## Source of truth

- `src/` — runtime implementation.
- `schemas/` — FigureSpec contract.
- `recipes/` — stable recipe registry.
- `packages/skill/` — canonical Skill source.
- `examples/golden/` — deterministic regression cases.
- `references/legacy/` — read-only development/provenance knowledge.

`packages/plugin/tikz-funfig/` is a generated portable distribution bundle. Do not maintain its runtime or Skill copies by hand. Change the source directories above, then run `./scripts/sync_plugin_package.sh`.

## Required development flow

For a new stable capability:

1. update the FigureSpec/schema contract if needed;
2. update renderer/recipe/method behavior;
3. add or update a golden case;
4. add regression coverage;
5. update the canonical Skill/documentation;
6. synchronize the portable Plugin;
7. run `./scripts/check.sh` and `git diff --check`.

Do not make the runtime depend on `references/legacy/`. Promote proven semantics into `src/`, `schemas/`, `recipes/`, and golden cases instead.

## Git and release rules

- Keep `main` runnable.
- One logical topic per commit; do not mix unrelated edits.
- Use the commit prefixes documented in `docs/GIT_WORKFLOW.md`.
- Do not commit generated PDFs, `.funfig` state, TeX build files, caches, or non-canonical IconKitchen exports.
- Never force-push `main` or rewrite published release tags.
- Releases require a clean tree, a `CHANGELOG.md` entry, passing tests, an annotated `vX.Y.Z` tag, and a push through `./scripts/release.sh X.Y.Z`.

## Documentation map

- Development: `docs/DEVELOPMENT.md`
- Git/commit workflow: `docs/GIT_WORKFLOW.md`
- Release/versioning: `docs/RELEASE.md`
- Codex install/update/rollback: `docs/INSTALL_UPDATE.md`
- Plugin packaging/distribution: `docs/PLUGIN_DISTRIBUTION.md`
- Architecture: `docs/architecture.md`

