# TIKZ-FunFig method catalog

This directory records the semantic promotion of useful historical TikZ/PGFPlots helpers.

The rule is: **preserve the behavior, not the old macro API**. Historical helpers such as
`\iiplot`, `\calxy`, `\addpoint`, and `\addsymbol` remain provenance; new figures should
use FigureSpec fields so the behavior is portable through the Skill and Codex Plugin.

`legacy-methods.json` is the audit table. A method marked `promoted` has a stable FigureSpec
representation and renderer support. `absorbed` means the old helper's intent is represented
by a more general structured field and should not be copied into generated TeX.

The catalog also records method-level migration behavior. Legacy `\iiplot` / `\iipolt`
calls with one portable `splot` statement are promoted to `implicit` data sources; simple
gnuplot `plot` bodies are preserved as managed `raw_gnuplot`. Complex multi-command bodies
or TeX-macro-dependent scripts stay explicit migration warnings rather than being guessed.

Current promoted interaction methods also include multiple named intersections, coordinate
label templates, and TikZ spy/detail lenses. These belong to the semantic method layer and
can be composed with any compatible recipe instead of becoming separate figure families.
