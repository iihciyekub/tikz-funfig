# Sourced Expert TikZ mode

Use when the requested geometry/notation/composition cannot be represented by a
stable Recipe without losing meaning. It expands practical reach without
pretending every TikZ feature is implemented in FigureSpec. Keep explicit
provenance for the official/manual knowledge used to justify the long-tail method.

1. Read `routing.md` and record why the best stable Recipe is insufficient.
2. Read `expert-patterns.md`; select a small explicit pattern set and focused
   knowledge queries before writing detailed coordinates.
3. Search shared knowledge; inspect relevant examples and the official manual
   section defining each required long-tail method. Inspect third-party source before use.
4. Set `render_mode: expert` in `figure.design.json`, record the reason in intent
   or assumptions, and keep actual official section IDs in `knowledge_sources`.
   Record supplementary card/example IDs there too when useful. For nontrivial
   figures also persist `routing.features`, `routing.unsupported_features`, and
   `routing.expert_patterns`.
5. Author standalone `<basename>.tex` using named coordinates, reusable styles,
   macros/loops for repeated structures, necessary libraries only, and explicit
   local data dependencies.
6. Run `expert-deps <dir>/figure.tex` when the source uses explicit packages or a
   non-default document class. Resolve missing `.sty`/`.cls` resources before
   compiling; do not delete a required package merely to make the file build.
7. Run `expert-build <dir>/figure.tex` with at least one trusted provenance
   reference: use `--source <official-section-id>` for official manual sections,
   or `--card <card-id>` for a verified curated knowledge card. Repeat either as
   needed and optionally set `--engine`. Do not pass arbitrary URLs or fabricate
   an unrelated PGF section merely to satisfy provenance for a third-party package.
8. Open `.funfig/expert-preview.png`, review using `visual-review.md`, repair and
   rebuild as needed. Record `expert-qa <tex> pass --note <actual observations>`.
9. If SVG was requested, derive it from the current PDF with `pdftocairo -svg
   <dir>/figure.pdf <dir>/figure.svg` and inspect the SVG too. This is an explicit
   export step; `expert-build` does not export SVG automatically.
10. Run `validate-design <dir>/figure.design.json --delivery` and deliver the
   design, editable TeX, PDF, requested SVG, data, and expert manifest.

Use the user's chosen basename consistently. The normal source name is
`figure.tex`; `.funfig/expert-manifest.json` records `mode: raw-expert` and source
hashes. Do not write a fake `figure.funfig.json` or patch a structured figure's
generated TeX while leaving a conflicting structured source authoritative.
For a mode transition, preserve the previous source deliberately (for example
an explicit archived copy), update the design, and make the new source of truth
clear. A routine revision stays in its existing mode and directory.

PDF remains the canonical compiled artifact. The design JSON is the common
intent/delivery schema; it does not make arbitrary Expert TeX regenerable from
FigureSpec. Never promise that it does. Expert support also does not imply formal
CAD, circuit EDA, UML, ER, or simulation semantics.

Do not enable shell escape for arbitrary TeX. The Expert builder rejects certain
execution syntax and does not enable shell escape. Prefer the managed gnuplot
Recipes for implicit/contour computation. If a required package/engine is missing,
report the dependency; do not remove essential geometry to disguise failure.

A successful one-off Expert result remains sourced Expert work. Promote recurring
patterns through knowledge/template, schema/renderer, golden cases, and regression
coverage before advertising a new stable capability.
