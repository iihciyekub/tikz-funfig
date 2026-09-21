# Diagram layout repair

When QA finds overlap or unreadable routing, repair in this order: semantic grouping/layout choice -> row/column/node gaps -> text width/canvas size -> anchors/routes -> minor font adjustment. Do not default to shrinking all text.

Check the figure at its Publication Profile target size. A layout that looks acceptable when zoomed in may still fail journal readability.

Source: TIKZ-FunFig QA rules. Example: `layout-repair`.
