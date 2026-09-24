# Interpreting reference images

Use for supplied photographs, screenshots, scans, sketches, and exemplar figures.
Open/view every relevant image before describing or reproducing it. A path, file
name, or OCR transcription does not replace seeing the image. If an attachment
cannot be accessed, explain what is missing; do not pretend to have inspected it.

## Assign reference roles

An image can have several explicit roles. Record each image's locator, roles,
features to adopt, and content not to transfer in `figure.design.json`:

- **Content:** entities, labels, arrows, visible measurements, or an apparatus to
  abstract. Preserve only what is legible and scientifically supported.
- **Structure/type:** hierarchy, grouping, panel organization, or reading order.
  Replace example content with the user's own content.
- **Style:** typography, palette, line weight, spacing, or annotation treatment.
  Do not transfer example data, module names, relationships, or scientific claims.

For “参考这种风格/类型，用我的内容画”, use style/structure roles; the user's
content determines the figure's meaning. For “照这张图重画”, preserve readable
content and structure. For “保留内容，重新排版”, preserve semantic relationships
and allow composition changes. Follow explicit fidelity instructions over defaults.
If references conflict, use each for its assigned role; ask only if the conflict
changes a meaningful relationship or requested fidelity.

## Extract before drawing

Separate: panel boundaries; entities/series; exact readable labels; edges and
arrow directions; containment; spatial/metric constraints; visual treatment.
For small text, inspect a crop or higher-resolution source when available. Mark
uncertain text/directions as unresolved instead of silently guessing. OCR is a
transcription aid, not scientific verification.

A photograph of equipment usually calls for a simplified labelled schematic.
Preserve relevant components, interfaces, geometry, and supplied measurements;
omit photographic clutter when the user requests abstraction. Do not invent
hidden components or metric dimensions from perspective. Explain any necessary
abstraction affecting the requested result.

For a plot screenshot, distinguish qualitative shape from numerical data. Use
original data if available. If only a visual reconstruction is possible, label
it as approximate and obtain clarification before presenting estimated values as
scientific measurements. Do not infer confidence intervals or precision from pixels.

## Compare the result appropriately

- Reproduction: compare labels, topology, panel arrangement, and requested fidelity.
- Redesign: compare semantic preservation, readability, and visual hierarchy.
- Style alignment: compare the selected visual features while checking that all
  content comes from the user's supplied material.

Do not optimize raw pixel similarity at the expense of labels or meaning. Photo
texture need not be traced when the requested result is a LaTeX schematic.
Reference images guide design; they are not implicitly embedded as a raster
background in a supposedly editable vector figure. If raster content is explicitly
needed, identify it and use an implementation path that actually supports it.

Use stable project-relative paths for locally retained references, or an honest
attachment label when no persistent path exists. Do not invent file locations or
copy a user's entire attachment directory. Reference-only images are not build
dependencies unless the figure actually embeds them.
