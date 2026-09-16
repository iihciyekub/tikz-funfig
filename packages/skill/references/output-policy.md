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
3. **Project default.** For a new figure with no explicit target, use
   `<active-project>/figures/<figure-id>/`.

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

## Update behavior

`init` deliberately refuses to overwrite an existing FigureSpec unless
`--force` is explicitly supplied. For normal revisions, read the existing
FigureSpec, modify the requested structured fields, and run `render`/`build`.

Never write normal user outputs under `~/.codex/plugins/cache/`, the portable
Plugin package, or `.agents/skills/`.
