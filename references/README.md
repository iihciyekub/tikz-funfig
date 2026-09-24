# TIKZ-FunFig reference knowledge base

This directory contains historical source material used to design and verify
TIKZ-FunFig. It is **development knowledge**, not Plugin runtime content.

Pinned external/official upstream material does not belong here; keep it under
`sources/`. This directory is now reserved for project-local legacy provenance
and promoted-method mapping.

## Promotion model

```text
references/legacy/
    historical notes, paper sources, data-generation provenance
        ↓ extract reusable semantics
recipes/ + schemas/ + src/
        ↓ verify against real figures
examples/golden/
        ↓ package only stable runtime behavior
packages/plugin/tikz-funfig/
```

Stable behavior must never depend at runtime on a file under `references/`.
When a historical example becomes important to the product, promote the
behavior into a Recipe/Schema capability and add a self-contained golden case.

## Legacy collections

- `legacy/tikz-memo/` — broad TikZ/PGFPlots/LaTeX technique notes.
- `legacy/pgfplots-memo/` — compact PGFPlots parameter and plotting examples.
- `legacy/publication-sustainability-1485080/` — source figures and data from a
  historical publication workflow used as provenance for publication recipes.

## Retention policy

Keep lightweight, inspectable knowledge sources in Git:

- `.tex`, `.sty`, `.md`;
- small `.dat`, `.csv`, and extensionless scientific data files;
- extracted historical `.py` calculation sources.

Do not retain generated or machine-specific material here:

- rendered `.pdf`, `.svg`, or raster previews;
- LaTeX/PGFPlots build intermediates;
- bundled font binaries;
- Jupyter checkpoints and notebook output containers after their computation
  cells have been preserved as plain Python source.

Exact data duplicates may remain when they make separate historical figures
self-contained. Do not deduplicate a few kilobytes at the cost of obscuring
which inputs belonged to which figure.

## Editing rule

Treat `legacy/` as mostly frozen provenance. Fix broken paths or documentation
when repository organization changes, but implement new product behavior under
`schemas/`, `recipes/`, `src/`, and `packages/skill/`.
