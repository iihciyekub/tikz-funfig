# Nodes and anchors

Give every reusable node a stable ID. Connect edges to node boundaries or explicit anchors (`north`, `south`, `east`, `west`, corners) instead of manually calculating line endpoints.

Use `inner sep`, minimum dimensions, and `text width` to control readable boxes. Explicit anchors override automatic boundary intersection only when routing needs it.

Source: PGF/TikZ 3.1.11a node chapters. Example: `node-anchors`.
