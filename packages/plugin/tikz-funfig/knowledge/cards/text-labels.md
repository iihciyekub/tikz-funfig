# Academic text and labels

Design labels for the final physical figure size. Set a reasonable `text width`, use explicit line breaks only when they improve hierarchy, and keep text centered or intentionally aligned.

Plain labels must escape TeX-special characters. Mathematical notation should be explicitly marked as TeX/math instead of inferred from punctuation. Repair crowding with spacing/canvas changes before reducing font size.

Sources: PGF/TikZ node text behavior plus TIKZ-FunFig publication QA rules. Example: `text-label`.
