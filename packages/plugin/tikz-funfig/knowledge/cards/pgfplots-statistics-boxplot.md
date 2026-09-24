# PGFPlots statistics and boxplots

Use the `statistics` library for supported statistical plot handlers such as prepared boxplots and histograms. Prepared statistics are preferred when the values were computed in a validated analysis pipeline.

Do not calculate or infer statistical summaries inside the drawing layer unless a Recipe explicitly owns that computation and records it in the manifest.

Labels, sample groups, whisker conventions, and outlier definitions must remain tied to the user's analytical method.

