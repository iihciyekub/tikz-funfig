# Development Guide

## Repository roles

TIKZ-FunFig separates authored source, regression evidence, historical reference material, and distribution artifacts.

| Path | Role | Directly edit? |
| --- | --- | --- |
| `src/funfig/` | Runtime/renderer/build/migration implementation | Yes |
| `schemas/` | Canonical FigureSpec schema | Yes |
| `recipes/` | Recipe registry and capability contracts | Yes |
| `packages/skill/` | Canonical Skill package | Yes |
| `packages/skills/` | Canonical specialized Skills + explicit package manifest | Yes |
| `knowledge/` | Shared compiled cards/examples and official-manual section corpus | Yes |
| `themes/` | Structured-diagram appearance tokens | Yes |
| `profiles/` | Publication/output size and QA constraints | Yes |
| `examples/golden/` | Deterministic regression inputs/snapshots | Yes, deliberately |
| `sources/` | Pinned official/community upstream material and provenance manifests | Preserve/update deliberately; never runtime |
| `references/legacy/` | Historical/provenance knowledge | Normally no; preserve as reference |
| `references/methods/` | Mapping of promoted legacy semantics | Yes |
| `packages/plugin/tikz-funfig/` | Portable generated Plugin bundle | No; synchronize it |

The portable Plugin deliberately materializes runtime/Skill files so an installed Plugin does not depend on a source checkout. Shared knowledge is distributed once at Plugin root rather than copied into every Skill. All generated distribution copies are checked for consistency.

## Official manual development pipeline

`sources/official/pgf/` pins the PGF/TikZ 3.1.11a documentation source and
its derived PDF-index manifests. The optional `references/pgfmanual.pdf` copy
is pinned by SHA/page count when present. Both are development/provenance
inputs, not portable-Plugin runtime dependencies.

The LaTeX source-example corpus is rebuilt directly from the pinned upstream
`codeexample` environments. The importer verifies the source tree hash,
preserves source/section/line provenance, compares its renderable count with
PGF's own `extract.lua` when `texlua` is available, and compiles a deterministic
representative sample:

```bash
python3 scripts/build_source_example_corpus.py build
python3 scripts/build_source_example_corpus.py verify --compile-samples
```

PGFPlots 1.18.2 is pinned separately under `sources/official/pgfplots/`.
Its source examples use the same provenance/safety model while restoring
PGFPlots-specific library context before representative compilation:

```bash
python3 scripts/build_pgfplots_source_corpus.py build
python3 scripts/build_pgfplots_source_corpus.py verify --compile-samples
```

The searchable section corpus only needs Poppler (`pdfinfo`, `pdftotext`). Generating official PDF booklets additionally requires `qpdf` so pages are copied without re-rendering or re-encoding:

```bash
brew install qpdf
python3 scripts/build_manual_reference.py verify
python3 scripts/build_manual_reference.py corpus
python3 scripts/build_manual_reference.py pdfs
```

The PDF build verifies page count/page boxes and representative source-vs-output text/render parity. `pdfseparate`/`pdfunite`, Ghostscript rewriting, and PDFKit page copies are intentionally not used for formal booklets because testing showed unacceptable resource duplication or text-mapping drift.

## Adding a capability

Use the smallest stable abstraction proven by a real use case. Prefer promoting semantics from existing figures/methods over adding generic options with no demonstrated need.

The expected path is:

```text
requirement / proven legacy method
        ↓
FigureSpec field or Method contract
        ↓
renderer / recipe implementation
        ↓
golden case
        ↓
regression test
        ↓
knowledge card/example + Skill/docs
        ↓
portable Plugin sync
```

Do not solve repeatable semantics with arbitrary raw TeX strings if a structured contract is practical. Raw gnuplot/TeX escape hatches are for cases that cannot yet be represented safely.

## Legacy references

`references/legacy/` is development knowledge, not runtime content. Production code, recipes, and the installed Plugin must not require those paths. When a historical idiom becomes stable, promote it and record the mapping in `references/methods/`.

## External source material

`sources/` is the canonical home for pinned official/community upstream
material. Keep each source registered in `sources/registry.json`, preserve its
license files, and write only normalized/searchable results to `knowledge/`.
The portable Plugin must work with the entire `sources/` tree absent.

## Generated files

The repository does not keep reproducible PDF/build output. Run `./scripts/clean_repo.sh` before release or when local test artifacts accumulate. Golden `.tex` snapshots are intentional source-controlled regression artifacts; generated `figure.tex` files outside those explicit snapshots remain ignored.

## Required checks

Before committing behavior changes:

```bash
./scripts/sync_plugin_package.sh
./scripts/check.sh
git diff --check
```

Review the diff after synchronization. A source change that affects the portable bundle should produce matching generated bundle changes.

