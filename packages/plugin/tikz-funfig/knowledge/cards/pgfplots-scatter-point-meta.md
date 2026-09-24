# PGFPlots scatter and point meta

Use `scatter` and `point meta` when marker appearance carries a third variable or category. Keep coordinate values and visual metadata separate so color, marker, or labels can change without altering positions.

Prefer explicit metadata columns for reproducible scientific plots. If classes are categorical, preserve their labels in the source data or FigureSpec rather than encoding meaning only through raw numeric colors.

Always provide a legend, colorbar, label, or other decoding mechanism when point appearance represents data.

