# Edge labels

Place edge labels at an explicit position and page-relative side (`above`, `below`, `left`, `right`). Keep label meaning independent from arrow direction and routing.

Use a subtle text backing when a label crosses a line-dense area. Do not rotate ordinary relationship labels unless it materially improves readability.

For a slanted branch whose caption should follow the path, set
`diagram.edges[].label_sloped: true` (FigureSpec 1.1). This uses TikZ's
`sloped` path-node placement and keeps the existing `label_position` and
`label_side` controls. Check the rendered result at publication width: long
labels on steep paths can still need more clearance or a different route.

Source: PGF/TikZ 3.1.11a node/edge syntax. Example: `edge-label`.
