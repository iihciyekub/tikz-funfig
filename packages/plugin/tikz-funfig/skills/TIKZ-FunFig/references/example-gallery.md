# TFF Example Gallery references

Use this reference whenever a user cites an immutable `TFF-xxxx` ID, asks to
reuse a Gallery example, or combines multiple Gallery examples by role.

## What a TFF ID means

A TFF ID is a permanent visual/source reference. It is not a Recipe ID, Template
ID, knowledge-card ID, or claim about scientific correctness. Never infer an
example from the number alone.

The public browser is:

`https://iihciyekub.github.io/tikz-funfig/`

Prefer the local registry for execution so installed work remains reproducible.

## Registry locations

Source checkout:

- registry: `gallery/registry.json`
- source cases: `examples/`

Installed portable Plugin:

- registry: `runtime/gallery/registry.json`
- source cases: `runtime/gallery/examples/`

Registry paths are stored relative to the source repository (for example
`examples/templates/flowcharts/feedback-loop`). In the installed Plugin, strip
the leading `examples/` and resolve the remainder under
`runtime/gallery/examples/`.

## Resolution contract

1. Match the requested ID exactly, case-insensitively.
2. If it is active and has no `canonical_id`, inspect that exact source case.
3. If it has `canonical_id`, preserve the requested ID as a stable alias but use
   the canonical entry as the primary visual/source template.
4. `gallery_visibility: hidden` affects browsing only; hidden aliases remain
   valid references.
5. If the ID is retired, do not reuse or reinterpret it. Report that it is retired.
6. If the ID is unknown, do not guess a nearby number.
7. Read the referenced source before drawing. Preserve the requested layout
   grammar, spacing, routing, typography, and visual hierarchy according to the
   user's requested role.
8. Replace example semantics with the user's supplied content. Example labels,
   data, causal claims, and domain meaning are not evidence for the new figure.

## Combining references

When the user assigns roles, honor them explicitly, for example:

- `TFF-0041` for layout;
- `TFF-0054` for edge/routing style;
- another TFF ID for annotation treatment.

When multiple IDs are supplied without roles, inspect them first. Combine only
compatible design dimensions; if they conflict in a way that materially changes
the requested figure, ask which property should dominate.

For a design record, a useful locator is `gallery:TFF-xxxx` with reference roles
such as `structure`, `style`, or `annotation`. Record the originally requested
alias even when implementation follows its canonical entry.

## External showcase provenance

Some Gallery entries are adapted showcase examples and include `origin_url`,
`license`, and `attribution`. Preserve that provenance when reusing substantial
source structure. The Gallery source is an editable reference implementation, not
permission to omit third-party attribution requirements.

## Version and availability

Current portable Plugins bundle the registry and source cases. If an older
installed Plugin lacks `runtime/gallery/registry.json`, treat it as an outdated
bundle rather than inventing a mapping. In a source checkout, repository
development may also resolve an ID with:

`python3 scripts/tff_gallery.py resolve TFF-0042`
