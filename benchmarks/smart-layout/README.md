# Measured layout evaluation

Run `PYTHONPATH=src python3 scripts/evaluate_smart_layout.py --out <project-output>`
for eleven deterministic cases in `tests/fixtures/smart-layout-cases.json`.
The suite includes real label changes, CJK, mathematics, large minimum heights,
decisions, nesting, multiple feedback paths, manual obstacle avoidance, and two
intentionally infeasible cases. It records first/final machine results, rounds,
elapsed time, hashes and semantic preservation. Image review remains separate.

`scripts/compare_elk_layout.py` is an optional development adapter for an already
installed `elkjs` module. It compares measured flat node-to-node graphs; portable
Plugin drawing has no Node/npm/ELK dependency. The adapter deliberately rejects
groups, hard constraints, and edge targets until those mappings are verified.
Official algorithm reference: https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html

Results from this run are documented in `docs/SMART_DRAWING_PLAN.md`; machine
passes never imply that arbitrary future figures are visually correct.
