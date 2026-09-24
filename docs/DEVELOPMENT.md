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
Its knowledge stack is generated directly from the pinned TeX documentation:
one importer builds the source-example corpus with PGFPlots-specific library
context and representative compilation, while another follows the manual
include tree and builds chapter/section/subsection search chunks without
round-tripping through PDF text extraction:

```bash
python3 scripts/build_pgfplots_source_corpus.py build
python3 scripts/build_pgfplots_source_corpus.py verify --compile-samples
python3 scripts/build_pgfplots_manual_corpus.py build
python3 scripts/build_pgfplots_manual_corpus.py verify
```

Curated `pgfplots-*` knowledge cards and compact project-authored examples form
the stable layer between Recipes and raw official corpus records. Plot Recipes
use `knowledge_ids` to bind to these cards. Paper-grade plot Templates are
promoted from regression-backed Goldens rather than copied from upstream manual
examples.

Curated community snapshots are pinned independently under
`sources/community/`. Runtime search never reads those raw snapshots
directly; rebuild their normalized corpus with:

```bash
python3 scripts/build_community_source_corpus.py build --compile-samples
python3 scripts/build_community_source_corpus.py verify
```

Community entries remain `source-extracted` reference knowledge by default.
Only representative cases that actually compile become `source-compiled`;
promotion to a TIKZ-FunFig Template or stable Recipe is a separate review step.

The searchable section corpus only needs Poppler (`pdfinfo`, `pdftotext`). Generating official PDF booklets additionally requires `qpdf` so pages are copied without re-rendering or re-encoding:

```bash
brew install qpdf
python3 scripts/build_manual_reference.py verify
python3 scripts/build_manual_reference.py corpus
python3 scripts/build_manual_reference.py pdfs
```

The PDF build verifies page count/page boxes and representative source-vs-output text/render parity. `pdfseparate`/`pdfunite`, Ghostscript rewriting, and PDFKit page copies are intentionally not used for formal booklets because testing showed unacceptable resource duplication or text-mapping drift.

## Figure QA

`funfig inspect` renders a preview and records machine checks in the figure
manifest before a human/agent visual review is marked. For schema 1.1 figures,
inspection also projects the natural PDF to the selected Publication Profile
width and records the projected dimensions/scale. When Poppler's `pdftotext`
is available, word bounding boxes provide a conservative text-size risk signal
after down-scaling. These metrics are warnings and evidence for visual review;
they do not replace checking labels, overlaps, arrows, whitespace, and semantic
fidelity in the rendered preview.

## Adding a capability

The six Skills share `packages/skill/references/workflow.md` plus conditional
image, composition, design-contract, Expert, and visual-review references.
`schemas/figure-design.schema.json` defines the additive intent/delivery sidecar;
`src/funfig/design.py` validates that contract and current delivery artifacts.
It intentionally interprets only the JSON Schema vocabulary used by this schema,
with unsupported keywords rejected; it is not a general JSON Schema engine.
When evolving the contract, update both supported vocabulary (if needed) and
behavioral tests. Existing FigureSpec-only CLI workflows remain compatible.

Skill descriptions and `agents/openai.yaml` retain normal implicit selection.
The general Skill frontmatter uses the lowercase `tikz-funfig` identifier
required by current Skill validation, while `agents/openai.yaml` and Plugin
metadata retain the public display name `TIKZ-FunFig`.

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
