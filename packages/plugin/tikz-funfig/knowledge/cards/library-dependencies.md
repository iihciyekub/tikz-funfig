# TikZ library dependencies

Compute `\usetikzlibrary{...}` from actual semantics: positioning, arrows.meta, fit, backgrounds, matrix, shapes.geometric, calc, intersections, topaths, and others only when needed. Sort and deduplicate libraries for deterministic TeX.

Do not load a large fixed library bundle merely because one diagram feature might need it.

Sources: PGF/TikZ manual plus TIKZ-FunFig deterministic build rules. Example: `library-deps`.
