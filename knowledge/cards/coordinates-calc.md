# Coordinates and calc

Use named coordinates and the `calc` library when a point is derived from stable geometry such as interpolation, offsets, or projections. Prefer semantic references like `(a.east)` and `($(a)!0.5!(b)$)` over repeated numeric coordinates.

Use absolute coordinates for roots or scientific geometry that is inherently numeric; use relative positioning for ordinary diagram layout.

Source: PGF/TikZ 3.1.11a coordinate calculation sections and `calc` library. Example: `calc-coordinate`.
