# Figure routing contract

Use this reference for complex reference images, mixed figures, or any request
where the correct implementation route is not obvious. The goal is deterministic
route selection, not a verbose explanation to the user.

## Route from meaning and required features

1. Read `scope-boundary.md`. First decide whether the request belongs to the core
   paper-figure boundary: plot, flowchart, framework, relation/model, basic
   schematic, or a mixed composition of those families.
2. Inventory only features that materially affect implementation, for example
   `3d-projection`, `repeated-components`, `transparent-layers`, `intersections`,
   `clipping`, `curved-routing`, `shared-axes`, `hidden-edges`, `cyclic-symmetry`,
   `dense-chords`, or `procedural-generation`.
3. Check `capabilities` and a small number of relevant Templates/knowledge hits.
   Prefer `product_scope=core`; use `long_tail` only under the explicit conditions
   in `scope-boundary.md`.
4. Compare the requested semantics with the best stable Recipe. Do not choose a
   Recipe merely because it can draw vaguely similar rectangles or lines.
5. Select the least-complex route that preserves meaning and requested fidelity.

## Decision rules

- **Structured:** a stable Recipe can preserve the required entities,
  relationships, geometry, and publication constraints without material loss.
- **Structured with promoted methods:** the Recipe is authoritative and only a
  documented supported method is needed for a local detail.
- **Expert:** forcing the task into a Recipe would distort meaningful geometry,
  omit a required visual mechanism, or make faithful reference reproduction
  impractical. Record why the best Recipe is insufficient.
- **Generative Expert:** choose Expert Mode plus `structure_model` when many
  visible primitives are instances of a compact mathematical rule **and** the
  user explicitly requested that long-tail geometry or is revising an existing
  managed generative figure. The generator model, not the emitted edge list, is
  the source of structural truth.
- **Mixed family:** use one composition and output directory, but coordinate only
  the needed specialist guidance. Do not use `groupplot` as a generic compositor.

Do not enter Expert Mode only because custom styling is easier there. Do not stay
Structured when doing so changes the scientific or diagrammatic meaning.
Do not proactively route an ordinary social-science, business, mathematical-model,
function/data, or flowchart request into generative/3D work merely because the
runtime can draw it. Prefer the simplest publication-ready representation inside
the core boundary. Do not expand a decorative reference detail into a new product
capability without an explicit scope decision.

## Persist a nontrivial route

For a complex or reference-led figure, add `routing` to `figure.design.json`:

```json
{
  "routing": {
    "features": ["3d-wireframe", "repeated-ellipses", "transparent-layers"],
    "recipe_candidate": "scientific-schematic",
    "unsupported_features": ["3d-wireframe"],
    "decision": "expert",
    "reason": "The stable schematic Recipe cannot represent the projected wireframe without losing the reference geometry.",
    "expert_patterns": ["projected-wireframe", "repeated-components", "layered-transparency"],
    "knowledge_queries": ["ellipse arc projection", "foreach repeated components", "background layers opacity"]
  }
}
```

Keep this record short. `features` describe implementation-relevant structure,
not every visible object. `unsupported_features` are gaps relative to the selected
Recipe, not a claim about what TikZ itself can do.

## Re-route only when evidence changes

Do not switch modes repeatedly because a first layout is unattractive. Repair
composition inside the chosen mode unless a concrete missing capability appears.
If switching from Structured to Expert, preserve the old source deliberately,
update the design record, and make the new source of truth explicit.
