# Figure design contract

New figures created through the Skills include `figure.design.json`, validated
against `runtime/schemas/figure-design.schema.json` in the Plugin (`schemas/` in
the source checkout). It records intent, reference interpretation, visual targets,
and delivery choices. FigureSpec or Expert TeX remains the executable source.
This sidecar is additive: existing FigureSpecs and CLI usage remain compatible.

Use this minimal shape, replacing example content with the user's actual task:

```json
{
  "schema_version": "1.0",
  "id": "fig-workflow",
  "task": "create",
  "family": "flowchart",
  "render_mode": "structured",
  "intent": "Explain the supplied preparation, analysis, and reporting sequence.",
  "content": {
    "must_preserve": ["Preparation -> Analysis -> Report"],
    "assumptions": ["Use a single-column layout because no width was specified."],
    "unresolved": []
  },
  "references": [],
  "appearance": {
    "layout": "Three vertically aligned process nodes with short forward arrows",
    "typography": "TeX serif text and matching mathematical notation",
    "theme": "journal-monochrome",
    "profile_id": "journal-single-column",
    "target_width_mm": 88,
    "minimum_text_pt": 7.5
  },
  "knowledge_sources": ["relative-positioning", "arrows-meta"],
  "routing": {
    "features": ["branch-merge"],
    "recipe_candidate": "flowchart",
    "unsupported_features": [],
    "decision": "structured",
    "reason": "The stable flowchart Recipe preserves the requested process semantics.",
    "expert_patterns": [],
    "knowledge_queries": ["flowchart branch merge"]
  },
  "review": {
    "reference_anchors": [],
    "repair_limit": 3
  },
  "delivery": {"basename": "figure", "formats": ["pdf"]}
}
```

`task` is create/reproduce/redesign/revise/repair/migrate. `family` is
plot/flowchart/framework/relation/schematic/mixed. `render_mode` is structured
or expert. Expert Mode requires nonempty `knowledge_sources`; supply actual
official section IDs used by `expert-build`, plus supplementary IDs as useful.

`routing` and `review` are optional for simple figures. Use them for complex,
reference-led, mixed, or Expert work. `routing.decision` must agree with
`render_mode`; `unsupported_features` describe gaps in the selected Recipe, not
general TikZ limitations. `review.reference_anchors` should contain only salient
features that make visual comparison more objective. `repair_limit` defaults to
three in the Skill workflow; it is a review discipline, not a hard renderer limit.

For dense rule-based geometry, add `structure_model`, optionally
`visual_density`, and a small numeric `search_space`. A `structure_model` currently
requires `render_mode: expert`; the generator model becomes the structural source
of truth and deterministic TeX is emitted from it. Example:

```json
{
  "structure_model": {
    "coordinate_system": "polar",
    "symmetry": {"group": "C16", "order": 16, "phase_deg": 90, "tolerance": 0.03},
    "generators": [
      {"id": "outer", "type": "ring_nodes", "parameters": {"count": 16, "radius": 5.0, "node_radius": 0.30, "phase_deg": 90}},
      {"id": "chords", "type": "complete_edges", "parameters": {"nodes": "outer"}},
      {"id": "center", "type": "center_node", "parameters": {"radius": 0.14}},
      {"id": "spokes", "type": "center_spokes", "parameters": {"nodes": "outer", "center": "center"}}
    ],
    "constraints": ["outer nodes are equally spaced", "center is at the origin"]
  },
  "visual_density": {"target": "light", "edge_opacity": 0.36},
  "search_space": [
    {"path": "visual_density.edge_opacity", "values": [0.28, 0.36, 0.44]}
  ]
}
```

`search_space` is only for numeric visual parameters. Do not search over user data,
topology, scientific values, or semantics. The current runtime supports bounded
polar graph, Cartesian/isometric lattice, small point-set Delaunay/Voronoi and
seeded Truchet tiling,
safe parametric expression and L-system, and projected-box visibility generators.
Unsupported generator families remain ordinary sourced
Expert TikZ until promoted deliberately.

For every relevant image, add a reference entry such as:

```json
{
  "locator": "attachment: user-provided reference image 1",
  "roles": ["structure", "style"],
  "adopt": ["Left-to-right grouping", "Thin black lines with restrained fills"],
  "do_not_transfer": ["Example module names", "Example numerical values"]
}
```

Use an actual local relative path when available; attachment labels are acceptable
for references that are not embedded build assets. `unresolved` lists blocking
content questions, not every optional aesthetic preference. Clear entries only
after resolving them; do not hide uncertainties to pass delivery validation.
Keep ordinary reasonable defaults in `assumptions` and proceed without requiring
approval of the JSON. Do not collect private or unrelated context in the record.

The design and rendered source must agree. These fields do not themselves apply
a theme, change figure geometry, verify meaning, or set font sizes. The agent must
implement and visually check them. Theme/Profile names describe targets even in
Expert/older plot paths where the corresponding automatic renderer fields do
not exist. Explicit user requirements override default visual settings.
Treat `target_width_mm` as the intended publication width budget unless the user
requires an exact export width; record that exact requirement in `must_preserve`
and measure the actual output. `validate-design` does not enforce PDF dimensions.

Use `validate-design <dir>/figure.design.json` before building. With a structured
FigureSpec present, validation also checks its validity, ID, basename, and formats
against the design. Preserve an existing explicit basename; default new output
to `figure`. PDF is required; SVG is optional.

After build and actual visual review, use `validate-design <dir>/figure.design.json
--delivery`. This additionally requires the canonical design filename, resolved
content questions, mode-specific artifacts, a successful build with matching
source/PDF hashes (and managed SVG hash), and recorded passing machine/visual QA.
The checker does not compare image meaning or enforce typography automatically.
Expert SVG is explicitly exported and visually checked; it is not hash-tracked
by the current Expert builder.

Update the design during revisions rather than creating alternate unversioned
briefs. A new source edit requires rebuilding/reviewing; a design-only change
still requires checking that the actual output satisfies the revised intent.
