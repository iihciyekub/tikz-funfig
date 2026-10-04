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
gallery/registry.json          immutable TFF Gallery ID mapping
examples/                      bundled Gallery source cases
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

The portable bundle contains only what an installed Plugin needs: Plugin manifest/interface assets, six Skills, runtime, schemas, recipes, themes, Publication Profiles, curated templates, the immutable TFF Gallery registry plus its lightweight source cases, compiled knowledge cards/examples, and the lightweight normalized PGF/TikZ corpus. It must not include `sources/`, `references/legacy/`, raw upstream repositories, the original/split manual PDFs, development notebooks, publication PDFs, fonts, or repository test/build state.

The shared `knowledge/` directory is distributed **once at Plugin root**. Specialized Skills remain thin and use their materialized `scripts/funfig.sh` wrapper to call the shared runtime. Do not copy the same cards into every Skill.

## Skill discovery and task scope

Descriptions front-load the actual trigger rather than repeating every supported
figure family. The general entry handles help, TFF reuse, mixed/unclear figures,
and cross-family work. Frameworks organize layers/groups/modules; relation
diagrams express variable paths, mediation and moderation; a branching layout
alone does not establish a process. All six retain implicit invocation.

Help-only requests load the capability menu and include the public
[Example Gallery](https://iihciyekub.github.io/tikz-funfig/), without initializing
figures. Actual drawing uses the shared local-revision, new-figure, or Expert
workflow. The website's displayed/copied prompts use the same semantic boundaries
and ask users for their own content, dimensions and output choices.
The Gallery supports Chinese and English, including example descriptions and
copyable prompts, with a remembered language preference.

Renderer regressions and documentation checks do not prove Skill behavior. Use
`benchmarks/skill-behavior/` for actual isolated Codex traces and independently
review generated previews. See its README for opt-in runs and evidence limits.

## Portable runtime contract

An installed copy must work when the source checkout and `references/pgfmanual.pdf` are unavailable. The portable regression test copies the generated Plugin to a temporary standalone directory and verifies knowledge search plus a structured flowchart build through a specialized Skill wrapper.

The ordinary installed Plugin may query:

```text
compiled knowledge cards
curated regression-backed templates
normalized PGF/TikZ, PGFPlots, and curated community source-example corpora
section-level official PGF/TikZ and PGFPlots manual corpora
Recipe/capability registry
immutable TFF Gallery IDs and bundled source cases
themes and Publication Profiles
```

The original 1323-page PDF remains a development/provenance source, not a runtime dependency.

## Bundle hygiene and size budget

`scripts/check_plugin_bundle.py` enforces a 25 MiB portable-bundle budget and
rejects raw source trees, legacy/manual reference directories, PDFs, font
binaries, LaTeX build intermediates, and common cache files. The budget is a
distribution guardrail rather than a target: normalized corpus growth should
prefer compact metadata/search records over copying upstream repositories.

The standalone regression test copies the Plugin to a temporary directory and
verifies official-manual, PGFPlots, and community knowledge search, curated
template inspection, and an actual flowchart build without access to the
repository source tree.

## Marketplace identity

- Marketplace: `tikz-funfig`
- Plugin: `tikz-funfig`
- Selector: `tikz-funfig@tikz-funfig`
- Git source: `git@github.com:iihciyekub/tikz-funfig.git`

The historical `tikz-funfig-local` registration is obsolete; update/install helpers remove it when encountered.

For the complete local-development, private-Git, release-tag, workspace, and
public-directory publication workflows, see
[CODEX_PLUGIN.md](CODEX_PLUGIN.md).

## Icons

Canonical source icons are `IconKitchen/macos/AppIcon128.png` and `AppIcon512.png`. `sync_plugin_package.sh` copies these into `packages/plugin/tikz-funfig/assets/` as composer icon/logo assets. Other IconKitchen exports are reproducible local outputs and are not versioned.
