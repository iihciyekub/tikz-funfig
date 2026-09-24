# PGFPlots table data

Use table input when coordinates come from measured, simulated, or computed data. Bind columns explicitly with `x=`, `y=`, `z=`, `meta=`, or error-column selectors instead of depending on column order.

Keep durable user data outside generated TeX when practical, and make relative data paths part of the figure artifact contract. Inline tables are appropriate for small self-contained examples and regression fixtures.

Do not silently discard rows or coerce units. Filtering and transformations should be explicit in FigureSpec or documented plot options.

