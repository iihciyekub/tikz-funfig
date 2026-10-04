# Product scope boundary

TIKZ-FunFig is primarily an academic-paper figure tool. Optimize reliability,
readability, editability, and publication fit for common research figures before
expanding the number of drawable object families.

## Core capability

The default product boundary is intentionally narrow:

1. **Social-science and business research frameworks** — layers, groups,
   containment, stakeholder/module organization, and labelled constructs supplied
   by the user. Variable paths and mediation/moderation use the relation workflow.
2. **Mathematical models and relationships** — equations or variables arranged
   as model/relationship diagrams, simple mathematical diagrams, and analytical
   relationships, variable paths, and mediation/moderation hypotheses that can be
   represented without inventing semantics.
3. **2D function and data plots** — analytic functions, data series, scatter,
   error bars, uncertainty bands, thresholds/regimes, comparisons, and ordinary
   publication multi-panel plots.
4. **Flowcharts** — ordered procedures, decisions, branches, merges, feedback,
   research procedures, and analysis workflows.
5. **Basic academic schematics** — restrained explanatory component/mechanism
   diagrams when they are naturally expressible with the existing schematic
   vocabulary.

For these families, prefer stable Recipes, curated Templates, and publication
profiles. Improve composition, labels, routing, typography, and QA before adding
new geometry families.

## Long-tail / experimental capability

Existing Expert and generative implementations may remain in the runtime for
backward compatibility and explicitly requested specialist work. Dense cyclic
graphs, lattices/tilings, fractals, procedural geometry, projected 3D boxes or
regular prisms, and other generative structures are **not the default product
boundary**. Do not advertise them in the main capability menu and do not route to
them proactively merely because they are technically available.

Use long-tail Expert/generative paths only when the user explicitly asks for that
specific complex geometry or when faithfully revising an existing managed figure
already using that path. Do not grow this area unless a future product decision
explicitly reopens the scope.

## Out of scope

Do not position TIKZ-FunFig as any of the following:

- electrical CAD/EDA, circuit simulation, or formal electronics validation;
- mechanical CAD, arbitrary 3D modelling, rendering, or perspective scene tools;
- animation/video generation;
- GIS/map projection or verified geographic cartography;
- photorealistic or general-purpose illustration;
- a statistical inference, econometrics, optimization, or mathematical proof
  engine (it may visualize supplied models, data, equations, and results);
- formal UML/BPMN/ER conformance unless a dedicated validated notation contract
  is explicitly added in the future.

When a request crosses this boundary, preserve the academic communication goal:
offer a simpler paper-ready abstraction if that still represents the user's
meaning. Do not silently invent unsupported formal semantics.
