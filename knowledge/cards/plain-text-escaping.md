# Plain-text escaping

For `label_format: plain`, escape `# $ % & _ { } ~ ^ \\` and convert explicit newlines to controlled TikZ line breaks. Do not run plain labels as arbitrary TeX.

For `label_format: tex`, preserve the user-provided mathematical/TeX expression and treat it as an explicit expert input.

Source: TIKZ-FunFig safety and reproducibility rules. Example: `plain-text`.
