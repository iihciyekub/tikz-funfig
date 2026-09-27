#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect(run_root: Path, cases_path: Path | None = None) -> dict[str, Any]:
    expected: dict[str, dict[str, Any]] = {}
    if cases_path is not None:
        fixture = load_json(cases_path)
        expected = {item["id"]: item for item in fixture.get("cases", [])}

    observed = {path.parent.name for path in run_root.glob("*/figure.design.json")}
    results: list[dict[str, Any]] = []
    for case_id in sorted(set(expected) | observed):
        case_dir = run_root / case_id
        design_path = case_dir / "figure.design.json"
        design = load_json(design_path) if design_path.is_file() else {}
        mode = design.get("render_mode")
        manifest_name = "expert-manifest.json" if mode == "expert" else "manifest.json"
        manifest_path = case_dir / ".funfig" / manifest_name
        manifest = load_json(manifest_path) if manifest_path.is_file() else {}
        qa = manifest.get("qa") or {}
        routing = design.get("routing") or {}
        patterns = list(routing.get("expert_patterns") or [])
        expected_case = expected.get(case_id) or {}
        expected_patterns = list(expected_case.get("expected_patterns") or [])
        missing_patterns = sorted(set(expected_patterns) - set(patterns))
        structure = design.get("structure_model") or {}
        generator_types = [item.get("type") for item in structure.get("generators", []) if isinstance(item, dict)]
        expected_generators = list(expected_case.get("expected_generators") or [])
        missing_generators = sorted(set(expected_generators) - set(generator_types))
        expected_route = expected_case.get("expected_route")
        route = routing.get("decision") or mode
        route_match = expected_route in (None, route)
        final_qa_pass = (
            qa.get("status") == "passed"
            and qa.get("visual_review") == "passed"
            and qa.get("machine_checks_passed") is True
        )
        review_path = case_dir / "reference-review.json"
        review = load_json(review_path) if review_path.is_file() else {}
        score_names = ("semantics", "geometry", "readability", "reference_alignment")
        scores = review.get("scores") if isinstance(review.get("scores"), dict) else {}
        score_pass = all(
            isinstance(scores.get(name), dict)
            and scores[name].get("result") == "pass"
            and isinstance(scores[name].get("evidence"), str)
            and bool(scores[name]["evidence"].strip())
            for name in score_names
        )
        reference_locator = expected_case.get("reference_url")
        locator_match = reference_locator in (None, review.get("reference_locator"))
        blind_pass = not expected_case.get("blind_required") or review.get("source_exposure") == "none"
        pdf_info = qa.get("pdf") if isinstance(qa.get("pdf"), dict) else {}
        size_check = qa.get("size_check") if isinstance(qa.get("size_check"), dict) else {}
        width = pdf_info.get("width_mm") if mode == "expert" else size_check.get("natural_width_mm")
        target_width = (design.get("appearance") or {}).get("target_width_mm")
        width_pass = (
            isinstance(width, (int, float)) and isinstance(target_width, (int, float))
            and 0 < width <= target_width
        )
        review_pass = (
            review.get("schema_version") == "1.0"
            and review.get("reviewer") in {"agent", "human"}
            and review.get("source_exposure") in {"none", "partial", "full"}
            and locator_match and blind_pass and score_pass
        )
        result = {
            "case_id": case_id,
            "design_id": design.get("id"),
            "route": route,
            "expected_route": expected_route,
            "route_match": route_match,
            "patterns": patterns,
            "missing_expected_patterns": missing_patterns,
            "generator_types": generator_types,
            "missing_expected_generators": missing_generators,
            "knowledge_sources": list(design.get("knowledge_sources") or []),
            "build_iteration": int(manifest.get("build_iteration") or 1) if manifest else 0,
            "review_history": list(qa.get("review_history") or []),
            "review_count": int(qa.get("review_count") or 0),
            "repair_cycles": int(qa.get("repair_cycles") or 0),
            "final_qa_status": qa.get("status", "missing"),
            "pdf": qa.get("pdf"),
            "reference_locator": review.get("reference_locator"),
            "source_exposure": review.get("source_exposure", "unrecorded"),
            "reviewer": review.get("reviewer"),
            "scores": scores,
            "reference_review_pass": review_pass,
            "actual_width_mm": width,
            "target_width_mm": target_width,
            "width_pass": width_pass,
            "passed": bool(manifest) and route_match and not missing_patterns and not missing_generators
            and final_qa_pass and review_pass and width_pass,
        }
        results.append(result)

    return {
        "schema_version": "1.1",
        "run_root": str(run_root),
        "case_count": len(results),
        "passed_count": sum(1 for item in results if item["passed"]),
        "failed_count": sum(1 for item in results if not item["passed"]),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect TIKZ-FunFig blind reference benchmark results")
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collect(args.run_root.resolve(), args.cases.resolve() if args.cases else None)
    output = args.output.resolve() if args.output else args.run_root.resolve() / "benchmark-results.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ok: {report['passed_count']}/{report['case_count']} benchmark cases passed -> {output}")
    return 0 if report["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
