# External source registry

`sources/` contains pinned upstream/reference material used to build searchable
knowledge for TIKZ-FunFig. It is development/provenance input, not Plugin
runtime content.

## Rules

- Register every upstream in `registry.json`.
- Pin a tag or commit; do not silently follow an upstream default branch.
- Preserve upstream license files and source-relative paths where practical.
- Keep normalized/searchable runtime material under `knowledge/`.
- Do not make `src/`, recipes, Skills, or the portable Plugin depend on this
  directory at runtime.
- Do not copy an entire upstream source tree into
  `packages/plugin/tikz-funfig/`.

## Layout

```text
sources/
├── registry.json
├── official/
│   ├── pgf/
│   │   ├── source.json
│   │   ├── upstream/
│   │   └── derived/
│   └── pgfplots/
└── community/
```

The registered official sources are the PGF/TikZ 3.1.11a documentation source
and PGFPlots 1.18.2 documentation source. The normalized PGF section corpus
remains in `knowledge/manual-index/`; normalized code examples from both
projects live in `knowledge/corpus/`.

