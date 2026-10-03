# TIKZ-FunFig portable plugin

This directory is generated/synchronized from the TIKZ-FunFig source project.

Stable authored files:

- `plugin.json` — portable Agent Plugins 1.0 manifest.
- `assets/icon.png` — composer icon derived from `IconKitchen/macos/AppIcon128.png`.
- `assets/logo.png` — plugin logo derived from `IconKitchen/macos/AppIcon512.png`.

Synchronized components:

- `skills/TIKZ-FunFig/` from `packages/skill/`.
- `runtime/src/funfig/` from `src/funfig/`.
- `runtime/schemas/` from `schemas/`.
- `runtime/recipes/` from `recipes/`.
- `runtime/gallery/registry.json` from `gallery/registry.json`.
- `runtime/gallery/examples/` from `examples/`, so immutable `TFF-xxxx`
  references resolve without the source checkout.

Do not make permanent feature edits only in the synchronized copies.
The manifest version is derived from the repository's canonical
`pyproject.toml` version; do not hand-edit it. Use
`python3 scripts/version.py set X.Y.Z` in the source repository and
`scripts/sync_plugin_package.sh` to regenerate the bundle.
