# PGFPlots axis and addplot

Use `axis` as the semantic coordinate system and keep each data series in a separate `\addplot`. Put publication-wide concerns such as labels, ticks, limits, legends, and scaling on the axis rather than repeating them per series.

Prefer explicit data bindings or functions over manual TikZ paths when the figure is fundamentally a quantitative plot. Keep the axis contract stable so the same FigureSpec can switch theme or Publication Profile without changing the scientific data.

Avoid mixing visual decoration with data semantics. A line style may change, but the represented variable, units, and series identity must remain user/data supplied.

