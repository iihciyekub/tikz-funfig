# TIKZ-FunFig style guide

These are defaults, not rigid rules. Preserve an existing manuscript's house style when one is already established.

## Visual hierarchy

- Primary data/curves should be the strongest visual element.
- Secondary/reference curves may use lower opacity or dashed/dash-dot lines.
- Highlighted regimes may use a pale fill with modest opacity; never make the fill stronger than the primary curves.
- Important points should use a small, high-contrast marker and a concise callout.
- Grid lines should be subtle and subordinate to data.

## Axes and ticks

- The default for ordinary 2D paper recipes is the `publication-offset` axis
  preset. It offsets the PGFPlots axis lines by 6.5pt, matching the spatial
  separation used by the publication golden cases.
- Publication ticks point inward, axis strokes stay thin, and declared axis
  endpoints remain visually aligned with endpoint tick marks.
- Publication annotation/callout text uses a near-opaque white backing
  by default (`fill opacity` 0.94) so dense text remains readable without
  competing with the plotted curves.
- Point and intersection marker fills stay separate from their label backgrounds.
  Use `label_style` to customize those labels; marker `style.color` supplies the
  default label text color when `label_style` is omitted.
- For text-heavy multi-panel figures, enlarge the panel canvas before shrinking
  fonts; widths around 8.8--9.2cm and heights around 6.6--7.0cm per panel are a
  useful starting range.
- Use `axes.preset: standard` for figures where an offset box is undesirable.
  A custom `axes.axis_line_shift` overrides the preset's default amount.
- The publication preset also uses inward ticks, thin academic axis/tick strokes,
  disables automatic limit enlargement, and guarantees a tick mark at both axis
  limits. Prefer making the first and last *labelled* major ticks equal to the
  declared min/max whenever those endpoint values are meaningful.
- Surface, contour, heatmap, and quiver recipes keep `standard` as their
  default because their 3D/view/colorbar geometry has different layout needs.
- Prefer explicit `xmin/xmax/ymin/ymax` when the scientific range is semantically meaningful.
- Use hand-picked ticks for thresholds, optima, breakpoints, or values discussed in the manuscript.
- Avoid excessive decimal digits. Format numbers deliberately with PGF number formatting.
- Axis labels should include both the quantity name and mathematical symbol when useful.
- Avoid reversing axes unless it is scientifically meaningful.

## Curves

- Use consistent line-width families rather than many unrelated widths.
- Distinguish curves with a combination of line pattern, marker, and color when the figure may be printed or viewed in grayscale.
- For piecewise behavior, prefer explicit segments or named paths rather than drawing a misleading continuous curve.

## Legends

- Keep legend entries mathematically concise.
- Place the legend where it does not cover important data; outside the axes is acceptable when the manuscript layout permits it.
- For dense figures, direct labels or compact callouts may be clearer than a large legend.
- Use consistent left alignment for multi-line legend text.

## Annotations

- Prefer named coordinates and relative placement (`calc`, anchors, positioning) to brittle raw offsets.
- Use `arrows.meta` and simple `Stealth`/`Latex` tips for academic callouts.
- Keep callout text small but readable at final publication size.
- Use concise coordinates or symbols; move long interpretation into the caption rather than the figure.

## Regions and intersections

- Use `name path` + `name intersections` when the intersection is logically defined by curves.
- Use `fillbetween` for areas bounded by curves.
- Use `soft clip` when only a specified x-domain should be shaded.
- Do not hard-code an intersection coordinate if it can be obtained robustly from named paths and the underlying plot is likely to change.

## Multi-panel figures

- Prefer `groupplots` for aligned scientific panels.
- Keep axis dimensions, fonts, line widths, and spacing consistent.
- Share labels/ticks where appropriate to reduce visual noise.
- Use panel labels `(a)`, `(b)`, etc. only when the manuscript references them.

## Source organization

For non-trivial figures, order source roughly as:

1. document class/packages;
2. TikZ/PGFPlots libraries;
3. color/style/macros;
4. data declarations or file references;
5. axis/groupplot setup;
6. primary plots;
7. regions/intersections;
8. annotations;
9. legend/final labels.

Avoid repeating the same style literal many times. Extract recurring properties into `\tikzset` or `\pgfplotsset` styles.

## Compatibility

- New PGFPlots sources default to `compat=1.18`.
- Use `standalone` for figure-only compilation.
- Prefer XeLaTeX for Chinese text or OpenType font requirements.
- `gnuplot` is part of the full TIKZ-FunFig toolchain and should be checked before implicit/raw-gnuplot figures are compiled.
- Enable `-shell-escape` only for inspected/trusted source that actually requires external gnuplot execution.
- Never embed a private/local font binary into a deliverable solely to make the figure compile; use an installed font or document the font requirement.
