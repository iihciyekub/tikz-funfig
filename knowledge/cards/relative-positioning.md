# Relative positioning

Load `positioning` and place dependent nodes with explicit directions and gaps such as `right=12mm of a`. Keep at least one stable root. This is the default choice for small flowcharts and conceptual frameworks.

Do not build long dependency cycles in placement. Business feedback edges may cycle; placement dependencies may not.

Source: PGF/TikZ 3.1.11a node/positioning material. Example: `relative-positioning`.
