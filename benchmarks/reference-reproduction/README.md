# Reference reproduction benchmark

This benchmark measures whether the Skill behaves like a figure-design agent, not
whether it can compile copied TikZ source. Run cases from a raster/screenshot or a
plain-language description without exposing the original TeX implementation.

For each case, record:

1. family and implementation-relevant feature inventory;
2. selected Structured/Expert route and why;
3. selected Expert patterns when applicable;
4. focused knowledge queries and provenance actually used;
5. build success;
6. number of visual review/repair cycles;
7. final semantic, geometry, reference, and publication-width QA result.

Each attempted case also needs `reference-review.json` next to
`figure.design.json`. Record `schema_version: "1.0"`, the `reference_locator`
(when the case fixture specifies one), `source_exposure` (`none`, `partial`, or
`full`), `reviewer` (`agent` or `human`), and a `scores` object. `scores` must
contain `semantics`, `geometry`, `readability`, and `reference_alignment`; each
needs `result: "pass"` and a non-empty, case-specific `evidence` note to pass.
Record actual defects as `fail` or `unknown` rather than filling a pass because
compilation succeeded. The collector reads measured PDF width from the QA
manifest and the target width from the design record. Cases declared in the
fixture but missing a run are counted as failures, preventing selection of only
successful outputs. A blind-required case fails if source exposure was recorded.

These scores are agent or human review evidence, not automatic image similarity
or independent adjudication. Keep the original TeX hidden during the run; direct
PNG/PDF views are acceptable, and text extracted from a rendered PDF can help
transcribe small labels without exposing the implementation.

The default review budget is three repair cycles. A compile-only success is not a
benchmark pass. Reference images are intentionally not vendored here; use a local
licensed/test asset or a user-provided image and preserve its locator in the figure
design record.

`cases.json` provides route expectations for representative hard figure classes.
They are evaluation prompts, not stable Recipe claims.

After a run, collect machine-readable results with:

```bash
python3 benchmarks/reference-reproduction/collect_results.py \
  /path/to/run-root \
  --cases benchmarks/reference-reproduction/cases.json
```

The collector reads each design, rubric, and `.funfig` manifest; checks route,
pattern, four review dimensions, source exposure, and actual final width; then
writes `benchmark-results.json` into the run root.
