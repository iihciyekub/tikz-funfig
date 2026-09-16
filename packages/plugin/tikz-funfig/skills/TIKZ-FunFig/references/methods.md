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

## Already promoted methods

`series[].name_path` + `intersection` annotations preserve named-path intersections, and
`regions[].type: "between"` preserves fill-between / soft-clip semantics.
