#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
RUNTIME_INIT = ROOT / "src/funfig/__init__.py"
HELPER = ROOT / "scripts/tff"
PLUGIN_MANIFEST = ROOT / "packages/plugin/tikz-funfig/plugin.json"

SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PYPROJECT_VERSION_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"$')
RUNTIME_VERSION_RE = re.compile(r'(?m)^__version__\s*=\s*"([^"]+)"$')
HELPER_VERSION_RE = re.compile(r'(?m)^VERSION\s*=\s*"([^"]+)"$')


def _replace(path: Path, pattern: re.Pattern[str], replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"error: could not update version in {path.relative_to(ROOT)}")
    path.write_text(updated, encoding="utf-8")


def canonical_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = PYPROJECT_VERSION_RE.search(text)
    if not match:
        raise SystemExit("error: pyproject.toml has no project version")
    version = match.group(1)
    if not SEMVER_RE.fullmatch(version):
        raise SystemExit(f"error: canonical version is not X.Y.Z: {version}")
    return version


def set_version(version: str) -> None:
    if not SEMVER_RE.fullmatch(version):
        raise SystemExit("error: version must be X.Y.Z")
    _replace(PYPROJECT, PYPROJECT_VERSION_RE, f'version = "{version}"')
    sync_derived()


def sync_derived() -> None:
    version = canonical_version()
    _replace(RUNTIME_INIT, RUNTIME_VERSION_RE, f'__version__ = "{version}"')
    _replace(HELPER, HELPER_VERSION_RE, f'VERSION = "{version}"')
    manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    manifest["version"] = version
    PLUGIN_MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"ok: synchronized derived version files -> {version}")


def _extract(path: Path, pattern: re.Pattern[str], label: str) -> str:
    match = pattern.search(path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"error: could not read {label} version")
    return match.group(1)


def check() -> None:
    version = canonical_version()
    observed = {
        "src/funfig/__init__.py": _extract(
            RUNTIME_INIT, RUNTIME_VERSION_RE, "runtime"
        ),
        "scripts/tff": _extract(HELPER, HELPER_VERSION_RE, "tff helper"),
        "packages/plugin/tikz-funfig/plugin.json": str(
            json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8")).get("version", "")
        ),
    }
    mismatches = {
        path: value for path, value in observed.items() if value != version
    }
    if mismatches:
        details = ", ".join(f"{path}={value!r}" for path, value in mismatches.items())
        raise SystemExit(
            f"error: version drift from pyproject.toml={version!r}: {details}; "
            "run 'python3 scripts/version.py sync'"
        )
    print(f"ok: version {version} is consistent across runtime, helper, and Plugin")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage TIKZ-FunFig's canonical package version."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("get", help="Print the canonical pyproject.toml version.")
    commands.add_parser("sync", help="Synchronize derived runtime/helper/Plugin versions.")
    commands.add_parser("check", help="Fail if a derived version has drifted.")
    setter = commands.add_parser("set", help="Set X.Y.Z in pyproject.toml and sync derivatives.")
    setter.add_argument("version")
    args = parser.parse_args()

    if args.command == "get":
        print(canonical_version())
    elif args.command == "sync":
        sync_derived()
    elif args.command == "check":
        check()
    else:
        set_version(args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
