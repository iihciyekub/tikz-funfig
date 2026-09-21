# Curved edges

Use a signed bend for feedback or parallel relationships where a straight edge would collide or become ambiguous. Positive values map to `bend left`, negative to `bend right`; zero should fall back to straight routing.

Prefer one clear bend over arbitrary Bézier control points. If many curves are required, reconsider the node layout first.

Source: PGF/TikZ 3.1.11a to-path material. Example: `curved-edge`.
