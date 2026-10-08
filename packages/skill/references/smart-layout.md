# Measured layout and repair

For new adjustable FigureSpec 1.1 diagrams, use `diagram.layout.type: "auto"`,
with `direction: "right"` or `"down"`. Positions may be omitted. Labels, roles,
edge directions and group membership still come from the user. `build` measures
real TeX node bounds and replans to convergence, up to four passes; explicit text
widths, minimum sizes, shapes, CJK and formulas participate in that measurement.
Grid `auto_fit` also measures actual dimensions; explicit gaps remain minimum
center distances. Relative/manual positions keep their intended placement.

Represent user hard geometry with `layout.constraints`: `align-x`, `align-y`,
`equal-width`, `equal-height`, `order-x`, `order-y`, or `pin`. Each has `nodes`;
`pin` has one node and `x`/`y` in cm; order constraints can set a positive `gap`.
Apply equal size only to comparable roles. Pins and scientific geometry take
priority over aesthetic placement. Conflicts are reported, never silently dropped.

Use `templates search "<structural terms>" --spec <spec> --json` to inspect
declared node/decision ranges, label density and target-width fit. Exclusion is
an adaptation warning, not proof that a redesigned template is impossible.
Exact TFF lookup remains exact and bypasses fuzzy ranking.

For an actual layout defect or a complex adjustable graph, run:

```sh
<absolute-skill-path>/scripts/funfig.sh optimize <spec> --design <design>
```

This compares at most three compositions and makes at most three repair rounds
per composition. It tries measured local repairs, checks semantics/constraints
and final-width readability, saves candidates and previous source under
`.funfig/optimization/`, and adopts only an improvement or a clean validated
current layout. Manual/scientific positions are preserved unless the user's task
authorizes reflow, in which case use `--relayout`; explicit pins always hold.
Treat return code 1 as unresolved diagnostics, not successful delivery.

`layout.measure: true` adds node, group/title, label and path checks to a retained
manual/relative composition. `polyline` edges have editable `routing.points`
in cm. Curves use sampled paths and rectangles are conservative bounding boxes:
inspect any reported intentional mathematical/shape interaction in the preview.
Missing or stale measurement/text tools fail machine acceptance. Expert TeX uses
the same PDF text/size checks (`--target-width-mm`, `--minimum-text-pt`), but its
arbitrary geometry requires sourced manual repair and image review.

Read the optimization report's defect objects, prescribed actions, before/after
scores, hashes and rollback results. Do not change unrelated content or expand
the canvas merely to shrink it later. If no feasible composition exists, keep the
useful current artifact and explain which width/pin/content conditions conflict;
panel splitting or caption edits must preserve the user's intended information.

Always open the current preview and follow `visual-review.md` before `qa pass`.
The optimizer leaves visual review pending and never learns success from its own
score. Generic prescriptions live in shared `knowledge/layout-prescriptions.json`;
the user's figure/history are not copied into product knowledge.
