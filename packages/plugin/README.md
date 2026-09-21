# Plugin distribution

`packages/plugin/tikz-funfig/` is the generated portable Codex/OpenAI Plugin package.

It contains six discoverable Skills (one general compatibility entry plus plots,
flowcharts, frameworks, relations, and schematics), a bundled dependency-light
runtime snapshot, shared searchable knowledge, themes, and Publication Profiles.
It does **not** define a second FigureSpec dialect or renderer, and it does not
bundle the original PGF/TikZ manual PDF.

The package is refreshed from repository sources with:

```bash
./scripts/sync_plugin_package.sh
```

The repo-local marketplace is `.agents/plugins/marketplace.json`.

