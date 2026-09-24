# Release and Versioning Guide

## Versioning

TIKZ-FunFig uses semantic versioning.

`pyproject.toml` is the single manually managed version source. Runtime,
`tff`, and portable Plugin versions are derived from it. Use:

```bash
python3 scripts/version.py get
python3 scripts/version.py check
python3 scripts/version.py set X.Y.Z
```

Do not hand-edit the derived version constants.

- **PATCH** (`0.8.2 → 0.8.3`): bug fixes, docs/governance, packaging/install improvements, and backward-compatible maintenance.
- **MINOR** (`0.8.x → 0.9.0`): new Recipe/Method/schema capabilities that remain compatible with existing managed figures.
- **MAJOR** (`1.x → 2.0.0`): intentional incompatible FigureSpec, Plugin, artifact, or CLI contract changes.

Before 1.0, a breaking contract change should still be explicitly documented and normally receive a minor version bump at minimum.

## Release prerequisites

- working tree is clean;
- `CHANGELOG.md` contains a heading for the target version;
- target tag does not already exist;
- `origin` is configured;
- full local regression passes;
- portable Plugin can be synchronized from canonical sources.

## Release command

```bash
./scripts/release.sh X.Y.Z
```

The script:

1. validates the release state and target version;
2. updates the canonical package version and synchronizes runtime/helper/Plugin versions;
3. synchronizes the portable Plugin;
4. runs `./scripts/check.sh` and `git diff --check`;
5. creates `release: vX.Y.Z`;
6. creates annotated tag `vX.Y.Z`;
7. pushes `main` and the tag to GitHub;
8. runs the local Codex update when available.

Published tags must never be moved or rewritten. If a release has a defect, fix it in a new version.

See [CODEX_PLUGIN.md](CODEX_PLUGIN.md) for local development installs, Git
marketplace distribution, workspace publishing, and public Plugin submission.

## Changelog

Move relevant items from `[Unreleased]` into a dated `## [X.Y.Z] - YYYY-MM-DD` section before invoking the release command. Keep release notes focused on user-visible contracts and operational changes.

## Failure recovery

If the script fails before push, fix the local issue and inspect the commit/tag state before retrying. If `main` or a tag has already been pushed, do not rewrite it; make a follow-up patch release.

