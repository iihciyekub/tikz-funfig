# Scopes and reusable styles

Use named `\tikzset` styles for repeated appearance and a `scope` only for a deliberate local transform or override. Keep semantic roles in FigureSpec/Recipe; do not hide node/edge meaning inside opaque style names.

Prefer a small style vocabulary, deterministic option order, and local overrides only when the exception is meaningful. Avoid copying long option lists onto every node.

Source: PGF/TikZ 3.1.11a core syntax/path chapters. Example: `style-scope`.
