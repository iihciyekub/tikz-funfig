#!/usr/bin/env python3
"""Exercise actual Codex discovery and delivery in disposable local workspaces."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = Path(__file__).with_name("cases.json")
SKILL_READ = re.compile(r"(?:^|[/\\])skills[/\\]([^/\\\s'\"]+)[/\\]SKILL\.md")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def execution_evidence(events: list[dict]) -> tuple[set[str], str, bool]:
    """Use executed tool inputs, never a final answer claiming a skill was used."""
    inputs = []
    viewed = False
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item", {})
        kind = item.get("type", "")
        if kind == "command_execution" and item.get("exit_code") == 0:
            inputs.append(item.get("command", ""))
        elif kind == "mcp_tool_call" and not item.get("error"):
            # Code-mode calls carry their actual executed JavaScript here.
            inputs.append(json.dumps(item.get("arguments", {}), ensure_ascii=False))
            viewed |= "view_image" in item.get("tool", "") or bool(re.search(
                r"\bview_image\s*\(", str(item.get("arguments", {}).get("code", ""))))
        elif kind in {"image_view", "local_image_view"}:
            viewed = True
    text = "\n".join(inputs)
    return set(SKILL_READ.findall(text)), text, viewed


def user_files(workspace: Path) -> list[Path]:
    return [p for p in workspace.rglob("*") if p.is_file()
            and ".agents" not in p.relative_to(workspace).parts
            and p.name != "AGENTS.md"]


def semantic_label(value: str) -> str:
    """Accept the same literal label with a TeX math wrapper, not new content."""
    return value[1:-1] if len(value) > 2 and value.startswith("$") and value.endswith("$") else value


def setup(workspace: Path, plugin: Path, fixture: str | None) -> dict[str, str]:
    shutil.copytree(plugin, workspace / ".agents",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (workspace / "AGENTS.md").write_text(
        "This is a disposable local figure workspace. Complete the user's request. "
        "Use the locally available .agents/skills when the task calls for them. "
        "Keep all writes in this workspace. Do not install packages, access the network, "
        "change live applications, or delegate to other agents.\n", encoding="utf-8")
    if fixture == "data":
        (workspace / "measurements.tsv").write_text(
            "time\tvalue\terror\n0\t1\t0.1\n1\t2\t0.2\n2\t1.5\t0.15\n",
            encoding="utf-8")
    elif fixture in {"existing", "image"}:
        # A real rendered figure supplies raw input; no expected answer is exposed.
        source = ROOT / "examples/golden/flowchart-feedback/figure.funfig.json"
        spec = read_json(source)
        spec["id"] = "existing-flow"
        # The golden's natural width exceeds its single-column QA budget.
        # A style-only repair should start with valid QA, not an unrelated defect.
        spec["profile"] = {"id": "journal-double-column"}
        spec["outputs"] = {"basename": "figure", "formats": ["pdf"], "keep_build": False}
        directory = workspace / "existing"
        directory.mkdir()
        write_json(directory / "figure.funfig.json", spec)
        wrapper = workspace / ".agents/skills/funfig-flowcharts/scripts/funfig.sh"
        subprocess.run([str(wrapper), "build", str(directory / "figure.funfig.json")],
                       cwd=workspace, check=True, capture_output=True)
        subprocess.run([str(wrapper), "inspect", str(directory / "figure.funfig.json")],
                       cwd=workspace, check=True, capture_output=True)
        if not read_json(directory / ".funfig/manifest.json")["qa"]["machine_checks_passed"]:
            raise ValueError("the input fixture must have passing machine checks")
        if fixture == "image":
            shutil.copy2(directory / ".funfig/preview.png", workspace / "reference.png")
            shutil.rmtree(directory)
    return {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in user_files(workspace)}


def grade(case: dict, workspace: Path, events: list[dict], final: str,
          exit_code: int, originals: dict[str, str]) -> dict:
    skills, commands, viewed = execution_evidence(events)
    checks = {"completed": exit_code == 0 and any(e.get("type") == "turn.completed" for e in events)}
    expected = case.get("skills", [])
    explicit = next((name for name in expected
                     if "$" + ("tikz-funfig" if name == "TIKZ-FunFig" else name) in case["prompt"]), None)
    # Native $ mentions can inject SKILL.md before the turn; JSONL has no event
    # for that injection. Require actual resource use, not an artificial re-read.
    explicit_resource = explicit and any(f"skills/{name}/" in commands
                                        for name in (explicit, "TIKZ-FunFig"))
    checks["skill_selection"] = (bool(skills.intersection(expected)) or bool(explicit_resource)
                                 if expected else not skills)
    for forbidden in case.get("forbidden_skills", []):
        checks["avoid_" + forbidden] = forbidden not in skills
    for ref in case.get("forbidden_reads", []):
        checks["skip_" + ref] = ref not in commands
    if case.get("help_link"):
        checks["gallery_link"] = "https://iihciyekub.github.io/tikz-funfig/" in final
    if case.get("no_output"):
        checks["no_unrequested_files"] = set(str(p.relative_to(workspace)) for p in user_files(workspace)) <= set(originals)
    for phrase in case.get("answer_contains", []):
        checks["answer_" + phrase] = phrase.casefold() in final.casefold()
    if case.get("preserve_input"):
        checks["input_unchanged"] = all((workspace / name).is_file()
            and hashlib.sha256((workspace / name).read_bytes()).hexdigest() == digest
            for name, digest in originals.items() if name.endswith(".tsv"))
    designs = [p for p in workspace.rglob("figure.design.json") if ".agents" not in p.parts]
    if case.get("delivery"):
        checks["one_design"] = len(designs) == 1
        # Some Codex CLI versions omit native image-view calls from JSONL.
        # Missing telemetry is not proof of a view or a failure; review separately.
        if len(designs) == 1:
            path = designs[0]
            design = read_json(path)
            checks["family"] = design.get("family") in case["families"]
            wrapper = workspace / ".agents/skills/TIKZ-FunFig/scripts/funfig.sh"
            result = subprocess.run([str(wrapper), "validate-design", str(path), "--delivery"],
                                    cwd=workspace, capture_output=True, text=True)
            checks["delivery_valid"] = result.returncode == 0
            spec_path = path.with_name("figure.funfig.json")
            if spec_path.is_file():
                spec = read_json(spec_path)
                nodes = {n["id"]: semantic_label(n.get("label", ""))
                         for n in spec.get("diagram", {}).get("nodes", [])}
                labels = list(nodes.values())
                for label in case.get("labels", []):
                    checks["label_" + label] = label in labels
                for label in case.get("excluded_labels", []):
                    checks["exclude_label_" + label] = label not in labels
                if case.get("moderation"):
                    edges = spec.get("diagram", {}).get("edges", [])
                    by_id = {e.get("id"): e for e in edges}
                    checks["moderator_targets_path"] = any(nodes.get(e.get("from")) == "W"
                        and e.get("to_edge") in by_id
                        and nodes.get(by_id[e["to_edge"]].get("from")) == "X"
                        and nodes.get(by_id[e["to_edge"]].get("to")) == "Y" for e in edges)
                if case.get("fixture") == "existing":
                    original = read_json(ROOT / "examples/golden/flowchart-feedback/figure.funfig.json")["diagram"]
                    checks["repair_preserves_nodes"] = nodes == {n["id"]: n["label"] for n in original["nodes"]}
                    def endpoints(diagram):
                        return sorted((e["id"], e["from"], e.get("to"), e.get("to_edge"),
                                       e.get("arrows"), e.get("label")) for e in diagram["edges"])
                    checks["repair_preserves_relationships"] = endpoints(spec["diagram"]) == endpoints(original)
                    checks["repair_stays_in_place"] = path.parent == workspace / "existing"
                if case.get("fixture") == "data":
                    sources = spec.get("data_sources", [])
                    checks["data_bound_without_substitution"] = any(s.get("x") == "time" and s.get("y") == "value"
                        and s.get("type") == "file" and (path.parent / s.get("path", "")).is_file()
                        and (path.parent / s["path"]).read_bytes() == (workspace / "measurements.tsv").read_bytes()
                        for s in sources)
                    checks["measurement_error_bound"] = any(series.get("error_bars", {}).get("y", {}).get("column") == "error"
                        and series["error_bars"]["y"].get("dir") == "both" for series in spec.get("series", []))
            elif case.get("labels") or case.get("moderation"):
                checks["structured_semantics"] = False
            if case.get("reference_role"):
                checks["reference_role"] = any(case["reference_role"] in r.get("roles", [])
                                               for r in design.get("references", []))
    return {"id": case["id"], "passed": all(checks.values()), "checks": checks,
            "skills_read": sorted(skills), "exit_code": exit_code,
            "activation_evidence": "explicit-mention-and-resource-use" if explicit_resource
                else "successful-tool-read" if skills else "none",
            "image_tool_evidence": "observed" if viewed else "not-exposed-in-jsonl",
            "visual_review": "pending-independent-review" if case.get("delivery") else "not-applicable"}


def run_case(case: dict, output: Path, plugin: Path, timeout: int) -> dict:
    directory = output / case["id"]
    directory.mkdir()
    workspace = directory / "workspace"
    originals = setup(workspace, plugin, case.get("fixture"))
    write_json(directory / "originals.json", originals)
    command = ["codex", "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
               "--disable", "plugins", "--disable", "apps", "--disable", "memories",
               "--disable", "multi_agent", "--sandbox", "workspace-write", "--json",
               "-C", str(workspace), "-o", str(directory / "final.txt")]
    if case.get("fixture") == "image":
        command.extend(["--image", str(workspace / "reference.png")])
    # --image accepts multiple positional files; terminate options before PROMPT.
    command.extend(["--", case["prompt"]])
    started = time.monotonic()
    with (directory / "trace.jsonl").open("w") as trace, (directory / "stderr.txt").open("w") as stderr:
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=trace, stderr=stderr,
                                    timeout=timeout, text=True)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    try:
        events = load_events(directory / "trace.jsonl")
        final_path = directory / "final.txt"
        final = final_path.read_text() if final_path.exists() else ""
        report = grade(case, workspace, events, final, code, originals)
    except (OSError, ValueError, KeyError) as exc:
        report = {"id": case["id"], "passed": False, "exit_code": code, "error": str(exc)}
    report["elapsed_seconds"] = round(time.monotonic() - started, 1)
    report["usage"] = next((e.get("usage", {}) for e in reversed(events)
                            if e.get("type") == "turn.completed"), {}) if "events" in locals() else {}
    write_json(directory / "result.json", report)
    print(f"{case['id']}: {'pass' if report['passed'] else 'FAIL'} ({report['elapsed_seconds']}s)", flush=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory outside the source checkout")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--plugin", type=Path, default=ROOT / "packages/plugin/tikz-funfig")
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--jobs", type=int, default=2, choices=(1, 2, 3))
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("eval artifacts must stay outside the source checkout")
    if output.exists():
        parser.error("use a fresh output directory; previous traces are evidence")
    if not shutil.which("codex"):
        parser.error("codex exec is required; no simulated fallback is available")
    cases = read_json(args.cases)["cases"]
    if args.only:
        unknown = set(args.only) - {c["id"] for c in cases}
        if unknown:
            parser.error(f"unknown cases: {sorted(unknown)}")
        cases = [c for c in cases if c["id"] in args.only]
    output.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        results = list(executor.map(lambda case: run_case(case, output, args.plugin.resolve(), args.timeout), cases))
    report = {"schema_version": "1.0", "plugin_version": read_json(args.plugin / "plugin.json")["version"],
              "case_count": len(results), "passed_count": sum(r["passed"] for r in results),
              "results": results, "visual_acceptance": "requires-independent-review"}
    write_json(output / "results.json", report)
    print(f"deterministic behavior checks: {report['passed_count']}/{len(results)}; visual acceptance is separate")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
