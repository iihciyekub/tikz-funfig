# Plugin distribution

`packages/plugin/tikz-funfig/` is the portable Codex/OpenAI Plugin package.

It contains the same TIKZ-FunFig Skill plus a bundled, dependency-light
runtime snapshot (`runtime/src/funfig`, `runtime/schemas`, `runtime/recipes`).
It does **not** define a second FigureSpec dialect or renderer.

The package is refreshed from repository sources with:

```bash
./scripts/sync_plugin_package.sh
```

The repo-local marketplace is `.agents/plugins/marketplace.json`.

