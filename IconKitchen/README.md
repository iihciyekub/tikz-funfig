# TIKZ-FunFig plugin icon source

`IconKitchen/` contains the multi-platform icon export for TIKZ-FunFig.

The repository intentionally tracks only the canonical macOS 128 px and
512 px PNGs used to derive the Codex Plugin presentation assets. The broader
iOS/Android/web export remains local generated material.

- `macos/AppIcon128.png` -> Plugin `composerIcon`
- `macos/AppIcon512.png` -> Plugin `logo`

Run `scripts/sync_plugin_package.sh` after changing either canonical icon.
