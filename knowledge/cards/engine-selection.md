# TeX engine selection

Use pdfLaTeX for ordinary Latin/basic diagrams, XeLaTeX for CJK or system-font needs, and LuaLaTeX for Graph Drawing. Gnuplot/shell escape is required only for relevant PGFPlots computation, not for ordinary flowcharts.

If the user explicitly selects an incompatible engine, return a clear error and alternatives instead of silently changing it.

Source: TIKZ-FunFig build contract and PGF/TikZ engine requirements. Example: `engine-selection`.
