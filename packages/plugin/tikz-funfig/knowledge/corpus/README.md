# Source-example corpus

This directory contains normalized, runtime-searchable examples extracted from
pinned sources under `sources/`.

It is not a raw mirror. Every entry records provenance, source hashes,
section/line location, libraries/commands, coarse figure/layout traits, license
metadata, renderability, and safety flags.

Current files:

- `examples.jsonl` — normalized PGF/TikZ 3.1.11a source examples.
- `index.json` — PGF/TikZ deterministic counts and representative compile sample IDs.
- `pgfplots-1.18.2.jsonl` — normalized PGFPlots 1.18.2 source examples.
- `pgfplots-1.18.2.index.json` — PGFPlots deterministic counts and compile sample IDs.
- `sources.json` — compact runtime-safe provenance for included sources.

Rebuild and verify:

```bash
python3 scripts/build_source_example_corpus.py build
python3 scripts/build_source_example_corpus.py verify --compile-samples
python3 scripts/build_pgfplots_source_corpus.py build
python3 scripts/build_pgfplots_source_corpus.py verify --compile-samples
```

Raw source trees never belong here. A corpus example is reference knowledge;
it does not become a stable TIKZ-FunFig capability until promoted through a
Template/Recipe/Golden workflow.
