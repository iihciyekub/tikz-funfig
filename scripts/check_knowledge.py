#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_links() -> list[str]:
    errors: list[str] = []
    cards = load(KNOWLEDGE / "cards/index.json").get("cards", [])
    examples = load(KNOWLEDGE / "examples/index.json").get("examples", [])
    example_ids = {item["id"] for item in examples}
    for card in cards:
        if not (KNOWLEDGE / "cards" / card["file"]).is_file():
            errors.append(f"missing card file: {card['file']}")
        for example_id in card.get("example_ids", []):
            if example_id not in example_ids:
                errors.append(f"card {card['id']} references unknown example: {example_id}")
    for item in examples:
        if not (KNOWLEDGE / "examples" / item["file"]).is_file():
            errors.append(f"missing example file: {item['file']}")
    return errors


def compile_examples(include_optional: bool = False) -> list[str]:
    errors: list[str] = []
    examples = load(KNOWLEDGE / "examples/index.json").get("examples", [])
    compiled_files: set[tuple[str, str]] = set()
    for item in examples:
        if item.get("optional") and not include_optional:
            continue
        key = (item["file"], item["engine"])
        if key in compiled_files:
            continue
        compiled_files.add(key)
        engine = item["engine"]
        if shutil.which(engine) is None:
            errors.append(f"missing engine {engine} for {item['file']}")
            continue
        source = KNOWLEDGE / "examples" / item["file"]
        with tempfile.TemporaryDirectory(prefix="tff-kb-") as temp:
            result = subprocess.run(
                [engine, "-interaction=nonstopmode", "-halt-on-error", "-output-directory", temp, str(source)],
                cwd=source.parent, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            if result.returncode:
                tail = "\n".join(result.stdout.splitlines()[-20:])
                errors.append(f"compile failed: {item['file']} ({engine})\n{tail}")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--include-optional", action="store_true")
    args = parser.parse_args(argv)
    errors = check_links()
    if args.compile:
        errors.extend(compile_examples(args.include_optional))
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("ok: knowledge cards/examples are consistent" + (" and compile" if args.compile else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
