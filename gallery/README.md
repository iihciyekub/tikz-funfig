# TIKZ-FunFig Example Gallery

Every curated example case receives one immutable identifier such as \`TFF-0042\`.

- IDs are never reassigned to unrelated examples.
- Moving or renaming a case preserves its ID when the case's internal identity is unchanged.
- Removed cases move to \`retired\` and their IDs remain reserved.
- \`gallery/registry.json\` is the canonical mapping committed to Git.
- GitHub Pages renders the current examples into searchable preview cards.

Common commands:

\`\`\`bash
python3 scripts/tff_gallery.py check
python3 scripts/tff_gallery.py sync
python3 scripts/tff_gallery.py resolve TFF-0042
PYTHONPATH=src python3 scripts/tff_gallery.py build-site --output _site
\`\`\`

When adding, moving, or deleting examples, run \`sync\` and commit the registry change with the example change.
