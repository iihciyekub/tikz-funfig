# Real Skill behavior evaluations

This suite runs actual `codex exec --json` sessions against a snapshot of the
portable Plugin. It complements renderer/golden tests and the paper visual suite;
documentation keyword checks are not agent behavior evaluations.

The 24 cases cover six entrypoints, explicit/implicit discovery, negative controls,
framework versus relationship semantics, nonprocess branching, help links, exact
Gallery IDs/aliases/unknown IDs, missing data, and six complete figure deliveries.
The model sees only the user request, local Skills, and any raw fixture. Expected
answers and grading rules are not copied into its workspace.

Run outside the checkout with Codex authentication and the normal local TeX tools:

```bash
python3 benchmarks/skill-behavior/run_cases.py /tmp/tff-behavior-candidate
python3 benchmarks/skill-behavior/run_cases.py /tmp/tff-behavior-focus \
  --only help-how implicit-moderation nonprocess-layout negative-theory
```

The runner uses isolated `.agents/skills`, disables installed Plugins, apps,
memory and delegation, and uses a workspace-write sandbox. It neither installs
dependencies nor changes the installed Plugin or user configuration. It preserves
traces, final answers, generated workspaces and per-case results; choose a fresh
output directory for each run. A timeout/failure is recorded, not replaced with a
simulated pass. Auth/model availability failures also fail the run. No model is
hardcoded. Real runs consume normal Codex usage and are opt-in, not part of CI.

Deterministic graders use successful tool inputs for Skill-read evidence, enforce
help-only/no-output requests, check website links, input retention, design family,
delivery validity, supplied labels, reference roles, and moderation endpoints.
The result also records elapsed time. A final answer claiming to have used a Skill
or viewed an image does not count as tool evidence.

Native `$skill-name` mentions may inject the Skill before the turn without a
JSONL read event. Explicit cases therefore require the native mention plus actual
supporting-resource tool use, and report that evidence separately. Implicit cases
still require successful Skill reads. Do not force redundant reads just to please
the grader or claim that JSONL exposes native injection itself.

Some CLI versions also omit native image-view calls from JSONL. The report marks
missing image-tool telemetry as `not-exposed-in-jsonl`; it does not turn an agent's
self-report into evidence or count missing telemetry as a rendering failure.
Independent review of the current artifacts is required for every delivery.

Inspect all delivered previews independently for semantic correctness, geometry,
reference fidelity and readability at publication width. Recorded QA and a passing
delivery validator alone cannot establish that acceptance. Reports retain
`requires-independent-review` until that separate assessment; don't describe the
deterministic pass count as automatic aesthetic scoring.

Store concise reviewed results here; keep raw traces, PDFs, previews, credentials,
and `.funfig` build state outside Git.
