# Plugin Distribution Contract

## Source and generated layers

The repository is the source of truth. The installed Codex Plugin is generated from canonical project sources:

```text
packages/skill/               canonical Skill
packages/skills/              canonical specialized Skills + package manifest
src/funfig/                   canonical runtime
schemas/                      canonical FigureSpec schema
recipes/                      canonical Recipe registry
themes/                       canonical structured-diagram themes
profiles/                     canonical publication/output profiles
knowledge/                    canonical cards, verified examples, manual section corpus
examples/templates/           canonical curated regression-backed templates
sources/                      pinned upstream/provenance input (NOT distributed)
IconKitchen canonical icons
        ↓ scripts/sync_plugin_package.sh
packages/plugin/tikz-funfig/  portable Git marketplace Plugin
        ↓ GitHub
Codex marketplace snapshot
        ↓
~/.codex/plugins/cache/...
```

Do not manually maintain `packages/plugin/tikz-funfig/runtime/`, `knowledge/`, or bundled Skills. `sync_plugin_package.sh` materializes one compatibility/general Skill plus the five specialized Skills declared in `packages/skills/index.json`. The consistency regression test verifies that distribution copies match canonical sources.

## What belongs in the Plugin

The portable bundle contains only what an installed Plugin needs: Plugin manifest/interface assets, six Skills, runtime, schemas, recipes, themes, Publication Profiles, curated templates, compiled knowledge cards/examples, and the lightweight normalized PGF/TikZ corpus. It must not include `sources/`, `references/legacy/`, raw upstream repositories, the original/split manual PDFs, development notebooks, publication PDFs, fonts, or repository test/build state.

The shared `knowledge/` directory is distributed **once at Plugin root**. Specialized Skills remain thin and use their materialized `scripts/funfig.sh` wrapper to call the shared runtime. Do not copy the same cards into every Skill.

## Portable runtime contract

An installed copy must work when the source checkout and `references/pgfmanual.pdf` are unavailable. The portable regression test copies the generated Plugin to a temporary standalone directory and verifies knowledge search plus a structured flowchart build through a specialized Skill wrapper.

The ordinary installed Plugin may query:

```text
compiled knowledge cards
curated regression-backed templates
section-level official manual corpus
Recipe/capability registry
themes and Publication Profiles
```

The original 1323-page PDF remains a development/provenance source, not a runtime dependency.

## Marketplace identity

- Marketplace: `tikz-funfig`
- Plugin: `tikz-funfig`
- Selector: `tikz-funfig@tikz-funfig`
- Git source: `git@github.com:iihciyekub/tikz-funfig.git`

The historical `tikz-funfig-local` registration is obsolete; update/install helpers remove it when encountered.

## Icons

Canonical source icons are `IconKitchen/macos/AppIcon128.png` and `AppIcon512.png`. `sync_plugin_package.sh` copies these into `packages/plugin/tikz-funfig/assets/` as composer icon/logo assets. Other IconKitchen exports are reproducible local outputs and are not versioned.

