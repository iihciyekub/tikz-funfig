# Project output policy

TIKZ-FunFig may run from a Codex Plugin cache, a workspace Skill, or the source
repository. None of those locations is a default destination for a user's
figure artifacts.

## Resolution order

For every figure-generation request, resolve the figure directory in this
order:

1. **Explicit target wins.** If the user names a directory, generate and update
   the managed figure there.
2. **Managed figure stays in place.** If the requested figure already has a
   `figure.funfig.json` or `figure.design.json`, revise the canonical source and
   rebuild in the same folder. An existing Expert TeX figure also stays in place.
3. **Explicit project root.** If `--project-root` is supplied, use
   `<project-root>/figures/<figure-id>/`.
4. **Active-project default.** Otherwise use `FUNFIG_PROJECT_ROOT` when the host
   provides it, or the current working directory as the active project root, and
   create `<active-project>/figures/<figure-id>/`.

The active project means the user's current paper/research/code workspace, not
the directory containing the installed Plugin runtime.

## CLI forms

Explicit destination:

```bash
funfig init ./paper-assets/fig-demand --recipe publication-threshold
```

Project-default destination:

```bash
funfig init --project-root ./my-paper --id fig-demand --recipe publication-threshold
```

The latter resolves to `./my-paper/figures/fig-demand/`.

When the command is already running from the user's active project, the shorter
form is canonical:

```bash
funfig init --id fig-demand --recipe publication-threshold
```

This resolves to `./figures/fig-demand/`. Hosts that launch the runtime from a
different working directory may set `FUNFIG_PROJECT_ROOT` instead.

## Artifact formats

In structured mode `figure.tex` is generated; in Expert Mode it is authored.
PDF is the canonical compiled artifact and is
always included. `outputs.formats` defaults to `["pdf"]`; use
`["pdf", "svg"]` to request a derived `figure.svg`. SVG export uses
`pdftocairo` after a successful PDF build.

## Stable directory contract

For a new Skill-managed figure use this layout. Omit optional empty directories;
preserve an existing or explicitly requested artifact basename.

```text
<project>/figures/<figure-id>/
  figure.design.json       # common validated intent/reference/delivery record
  figure.funfig.json       # structured mode: canonical rendering specification
  figure.tex              # generated in structured mode; authored in Expert Mode
  figure.pdf              # canonical compiled output
  figure.svg              # only when requested
  data/                   # actual local data needed to reproduce the figure
  references/             # optional relevant retained input images
  .funfig/
    manifest.json         # structured mode build and QA state
    preview.png           # structured review preview
    build/                # disposable structured intermediates
```

Expert Mode uses the same visible design/TeX/PDF names but has no synthetic
FigureSpec. Its state files are `.funfig/expert-manifest.json`,
`.funfig/expert-preview.png`, and `.funfig/expert-build/`. See `expert-mode.md`.
The design JSON and corresponding source identify the mode unambiguously.
Extra formats such as PNG are exports only when explicitly requested and are
outside the current PDF/SVG delivery-format enum; do not claim schema support
for a format by silently adding a new enum value.

One requested figure owns one stable folder. Multiple figures use sibling IDs;
multiple panels of one composed figure share its folder. Keep temporary drafts
under `.funfig/tmp/`; do not deliver `final2`, `final-new`, or duplicate parallel
source files unless the user explicitly wants retained variants. Do not rename
or remove existing user assets merely to impose this layout.

Validate `figure.design.json` before rendering and with `--delivery` after actual
visual review. The design schema is separate from FigureSpec and does not replace
its validation. Old figures without a design sidecar remain supported by the CLI.

## Update behavior

`init` deliberately refuses to overwrite an existing FigureSpec unless
`--force` is explicitly supplied. For normal revisions, read the existing
FigureSpec, modify the requested structured fields, and run `render`/`build`.

Never write normal user outputs under `~/.codex/plugins/cache/`, the portable
Plugin package, or `.agents/skills/`.
