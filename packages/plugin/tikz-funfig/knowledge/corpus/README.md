# Source-example corpus

This directory contains normalized, runtime-searchable examples extracted from
pinned sources under `sources/`.

It is not a raw mirror. Every entry records provenance, source hashes,
section/line location, libraries/commands, coarse figure/layout traits, license
metadata, renderability, and safety flags.

Current files:

- `examples.jsonl` — one normalized source example per line.
- `index.json` — deterministic counts and representative compile sample IDs.
- `sources.json` — compact runtime-safe provenance for included sources.

Rebuild and verify:

```bash
python3 scripts/build_source_example_corpus.py build
python3 scripts/build_source_example_corpus.py verify --compile-samples
```

Raw source trees never belong here. A corpus example is reference knowledge;
it does not become a stable TIKZ-FunFig capability until promoted through a
Template/Recipe/Golden workflow.
