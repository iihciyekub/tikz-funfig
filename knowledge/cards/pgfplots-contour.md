# PGFPlots contours

PGFPlots can draw contours from external computation, Lua computation, or precomputed contour coordinates. Prefer `contour prepared` when reproducible contour coordinates are already available; it avoids hidden external computation.

Use `contour lua` only when the LuaLaTeX workflow is explicitly supported. Use gnuplot-backed contouring only through a Recipe that declares the external dependency and shell-execution requirement.

Contour levels are scientific parameters. Preserve user/data supplied levels and document how they were obtained.

