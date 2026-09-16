# Promoted TIKZ-FunFig methods

These methods preserve useful behavior from the historical local TikZ helpers without
requiring generated figures to import the old `.sty` / macro files.

## Implicit contour

Use a data source with `type: "implicit"`, either `equation` or `expression`, and optional
`level`, `samples`, and `isosamples`. The renderer derives gnuplot `xrange` / `yrange` from
the source domain or current axes, enables contour mode, disables the surface, and emits the
requested level. An equation such as `x^2 + y^2 = 1` is rendered as a zero contour. This is
the promoted form of `\iiplot`, `\iipolt`, and the old `\fun` helper.

## Curve probe

`annotations[].type: "curve_probe"` binds a named TikZ coordinate to `position` in `[0,1]`
on a series. It can render a marker and format x, y, or `(x,y)` with explicit `precision`.
This replaces the combined `\addpoint` + `\calxy` pattern.

## Curve label

`annotations[].type: "curve_label"` binds text to a relative series position and can keep
the text sloped with the path. It replaces `\addsymbol`.

## Coordinate reference

`annotations[].type: "coordinate_ref"` attaches formatted x/y values to any named TikZ
coordinate, including a semantic intersection. It replaces `\calxy`, `\calx`, `\caly`,
`\getX`, `\getY`, and `\getXY`.

Use `template` when the coordinate values belong inside a larger label. Supported placeholders
are `{x}`, `{y}`, `{xy}`, and `{ref}`. For example, `$I=({x},{y})$` keeps the mathematical
label stable while the intersection itself moves.

## Multiple intersections

An `intersection` annotation can use `names: ["I1", "I2", ...]` when the same two named
paths cross more than once. Each named point becomes available to later `coordinate_ref`
annotations. This promotes the historical `name intersections={...,by={a,b}}` pattern.

## Spy/detail lens

Use `annotations[].type: "spy"` with `at`, `in`, `magnification`, shape/size, and optional
connector settings to create a stable magnified detail view. The renderer first materializes
PGFPlots axis positions as named TikZ coordinates before invoking the spy library so the
deferred spy operation does not lose the axis coordinate system.

## Legacy method migration

`migrate-legacy` recognizes common `\iiplot` / `\iipolt` calls. A single portable `splot`
becomes an `implicit` source; a simple gnuplot `plot` body becomes managed `raw_gnuplot`;
`\addpoint` / `\addsymbol` tails become `curve_probe` / `curve_label`; simple named
intersections and `\calxy{...}` references are promoted to semantic annotations. Complex
gnuplot bodies remain migration warnings instead of being silently rewritten.

## Already promoted methods

`series[].name_path` + `intersection` annotations preserve named-path intersections, and
`regions[].type: "between"` preserves fill-between / soft-clip semantics.
