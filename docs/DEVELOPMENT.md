# Development Guide

## Repository roles

TIKZ-FunFig separates authored source, regression evidence, historical reference material, and distribution artifacts.

| Path | Role | Directly edit? |
| --- | --- | --- |
| `src/funfig/` | Runtime/renderer/build/migration implementation | Yes |
| `schemas/` | Canonical FigureSpec schema | Yes |
| `recipes/` | Recipe registry and capability contracts | Yes |
| `packages/skill/` | Canonical Skill package | Yes |
| `examples/golden/` | Deterministic regression inputs/snapshots | Yes, deliberately |
| `references/legacy/` | Historical/provenance knowledge | Normally no; preserve as reference |
| `references/methods/` | Mapping of promoted legacy semantics | Yes |
| `packages/plugin/tikz-funfig/` | Portable generated Plugin bundle | No; synchronize it |

The portable Plugin deliberately duplicates runtime/Skill files so an installed Plugin does not depend on a source checkout. That duplication is generated and checked for consistency.

## Adding a capability

Use the smallest stable abstraction proven by a real use case. Prefer promoting semantics from existing figures/methods over adding generic options with no demonstrated need.

The expected path is:

```text
requirement / proven legacy method
        ↓
FigureSpec field or Method contract
        ↓
renderer / recipe implementation
        ↓
golden case
        ↓
regression test
        ↓
Skill/docs
        ↓
portable Plugin sync
```

Do not solve repeatable semantics with arbitrary raw TeX strings if a structured contract is practical. Raw gnuplot/TeX escape hatches are for cases that cannot yet be represented safely.

## Legacy references

`references/legacy/` is development knowledge, not runtime content. Production code, recipes, and the installed Plugin must not require those paths. When a historical idiom becomes stable, promote it and record the mapping in `references/methods/`.

## Generated files

The repository does not keep reproducible PDF/build output. Run `./scripts/clean_repo.sh` before release or when local test artifacts accumulate. Golden `.tex` snapshots are intentional source-controlled regression artifacts; generated `figure.tex` files outside those explicit snapshots remain ignored.

## Required checks

Before committing behavior changes:

```bash
./scripts/sync_plugin_package.sh
./scripts/check.sh
git diff --check
```

Review the diff after synchronization. A source change that affects the portable bundle should produce matching generated bundle changes.

