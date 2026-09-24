#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m funfig doctor
python3 scripts/build_manual_reference.py verify
python3 scripts/build_source_example_corpus.py verify --compile-samples
python3 scripts/build_pgfplots_source_corpus.py verify --compile-samples
python3 scripts/check_knowledge.py --compile
python3 -m unittest discover -s tests -p 'test_*.py' -v

