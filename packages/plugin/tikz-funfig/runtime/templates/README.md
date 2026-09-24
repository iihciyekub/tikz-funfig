# Curated academic templates

Templates are editable, regression-backed starting points between raw knowledge
examples and stable Recipes. Each template directory contains:

- `template.meta.json` — family, Recipe hint, supported profiles/themes,
  dependencies, edit contract, and optional `design_fit` guidance describing
  suitable structures, label density, target width, adaptation notes, and
  common failure modes;
- `template.funfig.json` — canonical editable FigureSpec;
- `template.tex` — deterministic renderer snapshot.

Use a stable Recipe as the product capability contract. Use the closest curated
template to choose a proven structure and appearance, then edit the FigureSpec
without violating the template's locked semantic rules.

Raw upstream/source examples are not templates and must not be promoted here
without compilation, regression coverage, provenance review, and an explicit
edit contract.

Template search indexes `design_fit` when present. This lets the Skill search
for a composition problem such as "feedback return route" or "merge split"
instead of relying only on a figure-family name.
