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
   `figure.funfig.json`, revise that FigureSpec and rebuild in the same folder.
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

`figure.tex` is always generated. PDF is the canonical compiled artifact and is
always included. `outputs.formats` defaults to `["pdf"]`; use
`["pdf", "svg"]` to request a derived `figure.svg`. SVG export uses
`pdftocairo` after a successful PDF build.

## Update behavior

`init` deliberately refuses to overwrite an existing FigureSpec unless
`--force` is explicitly supplied. For normal revisions, read the existing
FigureSpec, modify the requested structured fields, and run `render`/`build`.

Never write normal user outputs under `~/.codex/plugins/cache/`, the portable
Plugin package, or `.agents/skills/`.
