#!/usr/bin/env python3
"""Build representative paper figures for an explicit visual review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from funfig.build import build_spec
from funfig.io import load_json, write_json_atomic
from funfig.qa import inspect_spec
from funfig.schema import validate_spec
from funfig.templates import get_template


def prepare(case: dict, directory: Path) -> tuple[dict, Path]:
    template = get_template(case["template_id"])
    spec = load_json(Path(template["spec"]))
    spec["id"] = case["id"]
    spec["outputs"] = {"basename": "figure", "keep_build": False}
    spec["metadata"] = {"benchmark": "paper-visual", "template_id": case["template_id"]}
    if "profile_id" in case:
        spec["profile"] = {"id": case["profile_id"]}
    for collection, key in (("nodes", "node_updates"), ("edges", "edge_updates")):
        updates = case.get(key, {})
        if not updates:
            continue
        actual_ids = {item["id"] for item in spec["diagram"][collection]}
        unknown = set(updates) - actual_ids
        if unknown:
            raise ValueError(f"{case['id']}: unknown {collection} overrides: {sorted(unknown)}")
        for item in spec["diagram"][collection]:
            item.update(updates.get(item["id"], {}))
    spec.get("canvas", {}).update(case.get("canvas_updates", {}))
    spec.get("axes", {}).update(case.get("axes_updates", {}))
    directory.mkdir(parents=True, exist_ok=True)
    spec_path = directory / "figure.funfig.json"
    write_json_atomic(spec_path, spec)
    validation = validate_spec(spec, spec_path)
    if not validation.ok:
        raise ValueError(f"{case['id']}: " + "; ".join(validation.errors))
    return spec, spec_path


def run(cases_path: Path, output_root: Path) -> dict:
    cases = load_json(cases_path)["cases"]
    results = []
    for case in cases:
        spec, spec_path = prepare(case, output_root / case["id"])
        build_spec(spec, spec_path)
        qa = inspect_spec(spec, spec_path)
        size = qa["size_check"]
        width = size["natural_width_mm"]
        target = case["target_width_mm"]
        results.append({
            "case_id": case["id"], "family": case["family"],
            "template_id": case["template_id"],
            "profile_id": case.get("profile_id"),
            "natural_width_mm": width, "target_width_mm": target,
            "width_pass": width is not None and width <= target,
            "machine_checks_passed": qa["machine_checks_passed"],
            "warnings": qa["warnings"],
            "review_focus": case["review_focus"],
            "preview": str(spec_path.parent / ".funfig/preview.png"),
        })
    report = {"schema_version": "1.0", "case_count": len(results), "results": results}
    write_json_atomic(output_root / "machine-results.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.json"))
    args = parser.parse_args()
    report = run(args.cases.resolve(), args.output_root.resolve())
    passed = sum(item["width_pass"] and item["machine_checks_passed"] for item in report["results"])
    print(f"machine and width checks: {passed}/{report['case_count']}; inspect every preview before visual QA")
    return 0 if passed == report["case_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
