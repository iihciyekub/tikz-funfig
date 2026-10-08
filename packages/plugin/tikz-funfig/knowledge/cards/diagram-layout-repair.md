# Diagram layout repair

When QA finds overlap or unreadable routing, repair in this order: semantic grouping/layout choice -> row/column/node gaps -> text width/canvas size -> anchors/routes -> minor font adjustment. Do not default to shrinking all text.

Check the figure at its Publication Profile target size. A layout that looks acceptable when zoomed in may still fail journal readability.

At a fixed target width, increasing natural canvas size and shrinking the result
back can reduce effective text size. Reflow groups, wrap labels, or split panels
before relying on enlargement. Grid gaps measure coordinate spacing rather than
guaranteed border-to-border clearance for unequal node shapes. Visually inspect
edge/label and group-title collisions; text-box checks alone do not cover them.

Source: TIKZ-FunFig QA rules. Example: `layout-repair`.

Structured 1.1 `auto` layout and grid `auto_fit` now measure actual TeX node bounds.
`measure: true` enables conservative object-addressable node/group/title/path QA.
Use `optimize` for bounded local repairs and alternative orientations; its report
keeps defect IDs, actions, before/after scores, hashes and rollback evidence.
Fixed scientific positions need explicit reflow authorization; pins always hold.
Executable constraints belong in FigureSpec, not freeform design prose. Missing
checks do not count as passes. Expert Mode shares final-width PDF/text checks.
See `packages/skill/references/smart-layout.md` and `knowledge/layout-prescriptions.json`.
