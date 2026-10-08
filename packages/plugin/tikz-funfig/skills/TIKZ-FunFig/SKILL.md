---
name: tikz-funfig
description: Handle TikZ figure help, exact TFF Gallery reuse, mixed or unclear academic figures, and cross-family repairs. Use a specialist for a clear family.
---

# TIKZ-FunFig

Turn supplied research content into editable LaTeX figures. Explicit user
instructions take precedence over workflow defaults, including style, destination,
formats, and whether the task is drawing, advice, or review only.

## Select the task

- **Help:** when asked how to use you/TIKZ-FunFig, how to start, what you can draw,
  or for examples, read [capability-menu.md](references/capability-menu.md).
  Include the [Example Gallery](https://iihciyekub.github.io/tikz-funfig/) and a
  relevant natural-language example. Answer directly; no drawing workflow or
  figure files are needed for a help-only request.
- **Exact TFF reference:** read [example-gallery.md](references/example-gallery.md)
  and resolve the supplied ID before choosing a composition or searching.
- **Clear figure family:** read only the matching specialist below.
- **Mixed/unclear figure or cross-family repair:** coordinate the needed families
  in one composition and directory; read [workflow.md](references/workflow.md).

| Figure meaning | Specialist |
| --- | --- |
| Functions, measured data, axes, uncertainty, plot panels | `funfig-plots` |
| Ordered procedures, decisions, branch outcomes, feedback | `funfig-flowcharts` |
| Layers, groups, containment, organization of modules | `funfig-frameworks` |
| Variable/model paths, mediation, moderation, labelled relationships | `funfig-relations` |
| Apparatus, components, mechanisms, meaningful spatial geometry | `funfig-schematics` |

Select by meaning, not by the presence of boxes, arrows, or an image. A converging
layout alone does not imply process order. For a mixed figure, consult only the
needed guidance; `groupplot` aligns plots, not arbitrary diagram-plus-plot panels.

The host loads Skills from metadata or explicit invocation. Read sibling guidance
at `../<skill>/SKILL.md` in the Plugin (`../skills/<skill>/SKILL.md` in this source
checkout); do not launch agents or ask the user to choose an internal category.

## Figure work

The shared [workflow.md](references/workflow.md) defines local revision, new
figure, and Expert paths plus source, execution, and acceptance requirements.
Carry forward established decisions rather than re-running selection on each edit.
Read [scope-boundary.md](references/scope-boundary.md) only when the request
crosses common academic figure families; retained long-tail support does not
expand an ordinary task.

For measured spacing, executable layout conditions, template suitability and
bounded defect repair, consult shared `smart-layout.md` when relevant. Preserve
scientific coordinates; finish by viewing the current preview.
