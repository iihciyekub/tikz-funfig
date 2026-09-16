# Plugin Distribution Contract

## Source and generated layers

The repository is the source of truth. The installed Codex Plugin is generated from canonical project sources:

```text
packages/skill/               canonical Skill
src/funfig/                   canonical runtime
schemas/                      canonical FigureSpec schema
recipes/                      canonical Recipe registry
IconKitchen canonical icons
        ↓ scripts/sync_plugin_package.sh
packages/plugin/tikz-funfig/  portable Git marketplace Plugin
        ↓ GitHub
Codex marketplace snapshot
        ↓
~/.codex/plugins/cache/...
```

Do not manually maintain `packages/plugin/tikz-funfig/runtime/` or the bundled Skill. The consistency regression test verifies that distribution copies match canonical sources.

## What belongs in the Plugin

The portable bundle contains only what an installed Plugin needs: Plugin manifest/interface assets, Skill, runtime, schemas, and recipes. It must not include `references/legacy/`, development notebooks, publication PDFs, fonts, or repository test/build state.

## Marketplace identity

- Marketplace: `tikz-funfig`
- Plugin: `tikz-funfig`
- Selector: `tikz-funfig@tikz-funfig`
- Git source: `git@github.com:iihciyekub/tikz-funfig.git`

The historical `tikz-funfig-local` registration is obsolete; update/install helpers remove it when encountered.

## Icons

Canonical source icons are `IconKitchen/macos/AppIcon128.png` and `AppIcon512.png`. `sync_plugin_package.sh` copies these into `packages/plugin/tikz-funfig/assets/` as composer icon/logo assets. Other IconKitchen exports are reproducible local outputs and are not versioned.

