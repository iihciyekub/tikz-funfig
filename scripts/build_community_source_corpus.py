#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCES_ROOT = ROOT / "sources/community"
REGISTRY = ROOT / "sources/registry.json"
CORPUS_ROOT = ROOT / "knowledge/corpus"
OUTPUT = CORPUS_ROOT / "community.jsonl"
INDEX = CORPUS_ROOT / "community.index.json"
SOURCES_INDEX = CORPUS_ROOT / "sources.json"

COMMAND_RE = re.compile(r"\\([A-Za-z@]+)")
USEPACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}")
TIKZLIB_RE = re.compile(r"\\usetikzlibrary\{([^}]+)\}")
PGFPLOTSLIB_RE = re.compile(r"\\usepgfplotslibrary\{([^}]+)\}")
DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}")

SAFETY_PATTERNS = {
    "write18": re.compile(r"\\(?:immediate\s*)?write18\b"),
    "shell-escape": re.compile(r"--shell-escape"),
    "absolute-input": re.compile(r"\\(?:input|include)\s*\{\s*/"),
    "external-process": re.compile(r"\\(?:write|openout|read|openin)\b"),
}

FAMILY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("architecture", ("architecture", "neural network", "transformer", "attention", "encoder", "decoder", "gan", "autoencoder", "resnet", "lstm", "cnn", "gnn", "machine learning")),
    ("flowchart", ("flowchart", "workflow", "pipeline", "process", "execution", "cycle")),
    ("graph", ("graph", "network", "tree", "shortest path", "maximum flow", "hamiltonian")),
    ("plot", ("plot", "distribution", "curve", "surface", "histogram", "scatter", "heatmap", "axis")),
    ("geometry", ("geometry", "coordinate", "sphere", "torus", "lattice", "polygon", "convex hull")),
    ("schematic", ("schematic", "circuit", "device", "molecule", "experiment", "sampling", "modulation", "capacitor")),
]

LAYOUT_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("layered", ("layer", "encoder", "decoder", "pipeline", "stack")),
    ("grid", ("matrix", "grid", "table", "convolution")),
    ("radial", ("radial", "mindmap", "sphere")),
    ("tree", ("tree",)),
    ("left-to-right", ("pipeline", "encoder", "decoder", "flow", "sequence")),
    ("grouped", ("group", "module", "block")),
]

STYLE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("publication", ("paper", "publication", "scientific", "academic")),
    ("technical", ("architecture", "system", "network", "circuit", "diagram")),
    ("annotated", ("label", "annotation", "explain")),
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "example"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def simple_yaml_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    result: dict[str, Any] = {}
    title = re.search(r"^title:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    if title:
        result["title"] = title.group(1).strip().strip('"')
    tags: list[str] = []
    tag_block = re.search(r"^tags:\s*\n((?:\s+-\s+.*\n?)+)", text, flags=re.MULTILINE)
    if tag_block:
        tags = [
            line.split("-", 1)[1].strip().strip('"')
            for line in tag_block.group(1).splitlines()
            if "-" in line
        ]
    result["tags"] = tags
    description = re.search(
        r"^description:\s*(?:[>|]-?)?\s*\n((?:(?:\s{2,}|\t).*(?:\n|$))+)",
        text,
        flags=re.MULTILINE,
    )
    if description:
        body = " ".join(line.strip() for line in description.group(1).splitlines())
        result["description"] = re.sub(r"\s+", " ", body).strip()
    return result


def csv_values(matches: Iterable[str]) -> list[str]:
    values: list[str] = []
    for match in matches:
        values.extend(part.strip() for part in match.split(",") if part.strip())
    return sorted(set(values))


def libraries(code: str) -> tuple[list[str], dict[str, list[str]]]:
    tikz = csv_values(TIKZLIB_RE.findall(code))
    pgfplots = csv_values(PGFPLOTSLIB_RE.findall(code))
    combined = sorted(set(tikz + [f"pgfplots:{item}" for item in pgfplots]))
    return combined, {"tikz": tikz, "pgf": [], "pgfplots": pgfplots}


def packages(code: str) -> list[str]:
    values = csv_values(USEPACKAGE_RE.findall(code))
    for cls in DOCUMENTCLASS_RE.findall(code):
        if cls.strip() == "standalone":
            values.append("standalone")
    return sorted(set(values))


def commands(code: str) -> list[str]:
    common = {
        "addplot", "addplot3", "coordinate", "draw", "fill", "filldraw",
        "foreach", "matrix", "node", "path", "pic", "plot", "shade",
        "tikzset",
    }
    found = {f"\\{name}" for name in COMMAND_RE.findall(code) if name in common}
    return sorted(found)


def safety_flags(code: str) -> list[str]:
    return [name for name, pattern in SAFETY_PATTERNS.items() if pattern.search(code)]


def traits(text: str, rules: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    low = text.casefold()
    return [name for name, needles in rules if any(needle in low for needle in needles)]


def families(title: str, tags: list[str], summary: str, code: str) -> list[str]:
    probe = " ".join([title, *tags, summary])
    values = traits(probe, FAMILY_RULES)
    if "\\begin{axis}" in code or "\\addplot" in code:
        values.append("plot")
    if "\\matrix" in code:
        values.append("relation")
    if "\\begin{tikzpicture}" in code and not values:
        values.append("tikz")
    return sorted(set(values))


def make_entry(
    *,
    source: dict[str, Any],
    tex_path: Path,
    title: str,
    tags: list[str],
    summary: str,
    extra_aliases: list[str] | None = None,
) -> dict[str, Any]:
    code = tex_path.read_text(encoding="utf-8", errors="replace")
    libs, library_types = libraries(code)
    pkgs = packages(code)
    flags = safety_flags(code)
    family_values = families(title, tags, summary, code)
    probe = " ".join([title, *tags, summary, *(extra_aliases or [])])
    renderable = "\\begin{document}" in code and "\\begin{tikzpicture}" in code
    engine = "xelatex" if any(token in code for token in ("fontspec", "xeCJK", "ctex")) else "pdflatex"
    identity = tex_path.parent.name if tex_path.stem in {"template", "figure"} else tex_path.stem
    return {
        "id": f"{slug(source['source_id'])}-{slug(identity)}-{sha256_file(tex_path)[:8]}",
        "source_id": source["source_id"],
        "source_kind": "community",
        "source_version": source["version"],
        "source_locator": {
            "path": rel(tex_path),
            "line_start": 1,
            "line_end": max(1, len(code.splitlines())),
            "ordinal": 1,
            "section_path": [],
        },
        "title": title,
        "summary": summary[:1000],
        "figure_families": family_values,
        "layout_traits": traits(probe, LAYOUT_RULES),
        "style_traits": traits(probe, STYLE_RULES),
        "tags": sorted(set(tags + (extra_aliases or []))),
        "libraries": libs,
        "library_types": library_types,
        "packages": pkgs,
        "commands": commands(code),
        "keys": [],
        "engine": engine,
        "options": {},
        "code": code,
        "setup_code": "",
        "preamble": "",
        "pre": "",
        "post": "",
        "render_instead": "",
        "renderable": renderable,
        "compile_eligible": renderable and not flags,
        "safety_flags": flags,
        "skip_reason": None if renderable else "not-standalone-tikz",
        "verification": "source-extracted",
        "compile_status": "not-run",
        "license_ids": source["license_ids"],
        "source_hash": sha256_file(tex_path),
        "code_hash": sha256_text(code),
    }


def opentikz_entries(source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ROOT / source["source_root"]
    result: list[dict[str, Any]] = []
    paths = sorted(root.glob("templates/*/template.tex")) + sorted(root.glob("examples/*/figure.tex"))
    for tex_path in paths:
        meta_path = tex_path.with_name(
            "template.meta.json" if tex_path.name == "template.tex" else "figure.meta.json"
        )
        meta = load_json(meta_path) if meta_path.is_file() else {}
        result.append(
            make_entry(
                source=source,
                tex_path=tex_path,
                title=meta.get("name") or meta.get("id") or tex_path.parent.name,
                tags=[*meta.get("tags", []), *meta.get("domain", []), *meta.get("venue", [])],
                summary=meta.get("description", ""),
                extra_aliases=[meta.get("type", "")],
            )
        )
    return result


def janosh_entries(source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ROOT / source["source_root"] / "assets"
    result: list[dict[str, Any]] = []
    for tex_path in sorted(root.glob("*/*.tex")):
        meta = simple_yaml_metadata(tex_path.with_suffix(".yml"))
        result.append(
            make_entry(
                source=source,
                tex_path=tex_path,
                title=meta.get("title") or tex_path.stem.replace("-", " ").title(),
                tags=meta.get("tags", []),
                summary=meta.get("description", ""),
            )
        )
    return result


def petarv_entries(source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ROOT / source["source_root"]
    result: list[dict[str, Any]] = []
    for tex_path in sorted(root.glob("*/*.tex")):
        title = tex_path.parent.name.replace("_", " ").strip()
        result.append(
            make_entry(
                source=source,
                tex_path=tex_path,
                title=title,
                tags=["tikz", "publication figure"],
                summary=f"Community TikZ figure from PetarV-/TikZ: {title}.",
            )
        )
    return result


def community_sources() -> list[dict[str, Any]]:
    registry = load_json(REGISTRY)
    sources: list[dict[str, Any]] = []
    for item in registry.get("sources", []):
        if item.get("kind") != "community":
            continue
        manifest = load_json(ROOT / item["manifest"])
        manifest["source_root"] = item["local_root"]
        sources.append(manifest)
    return sources


def runtime_sources_payload() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    sources: list[dict[str, Any]] = []
    for record in registry.get("sources", []):
        if record.get("plugin_policy") != "normalized-only":
            continue
        source_manifest: dict[str, Any] = {}
        manifest_path = record.get("manifest")
        if manifest_path and (ROOT / manifest_path).is_file():
            source_manifest = load_json(ROOT / manifest_path)
        sources.append(
            {
                "id": record["id"],
                "kind": record["kind"],
                "project": record["project"],
                "upstream": record["upstream"],
                "revision": record["revision"],
                "version": source_manifest.get(
                    "version",
                    record.get("release_tag", record["revision"]),
                ),
                "license_ids": record.get("license_ids", []),
                "plugin_policy": record["plugin_policy"],
            }
        )
    return {"schema_version": "1.0", "sources": sources}


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
        digest.update(b"\0")
    return digest.hexdigest()


def validate_sources(sources: list[dict[str, Any]]) -> None:
    for source in sources:
        root = ROOT / source["source_root"]
        if not root.is_dir():
            raise SystemExit(f"missing source root: {root}")
        actual = tree_hash(root)
        if actual != source["tree_sha256"]:
            raise SystemExit(
                f"source tree hash mismatch for {source['source_id']}: "
                f"expected={source['tree_sha256']} actual={actual}"
            )
        license_path = ROOT / source["license_file"]
        if not license_path.is_file():
            raise SystemExit(f"missing license file for {source['source_id']}: {license_path}")
        tex_count = len(list(root.rglob("*.tex")))
        if tex_count != int(source["tex_file_count"]):
            raise SystemExit(
                f"tex count mismatch for {source['source_id']}: "
                f"expected={source['tex_file_count']} actual={tex_count}"
            )


def build_entries(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    handlers = {
        "opentikz-content": opentikz_entries,
        "janosh-diagrams": janosh_entries,
        "petarv-tikz": petarv_entries,
    }
    entries: list[dict[str, Any]] = []
    for source in sources:
        handler = handlers.get(source["source_id"])
        if handler is not None:
            entries.extend(handler(source))
    ids = [item["id"] for item in entries]
    if len(ids) != len(set(ids)):
        dupes = sorted(k for k, v in Counter(ids).items() if v > 1)
        raise SystemExit(f"duplicate community corpus ids: {dupes}")
    return entries


def compile_entry(entry: dict[str, Any]) -> tuple[bool, str]:
    latexmk = shutil.which("latexmk")
    engine = shutil.which(entry["engine"])
    if not latexmk or not engine:
        return False, "toolchain-unavailable"
    source_path = ROOT / entry["source_locator"]["path"]
    source_dir = source_path.parent
    with tempfile.TemporaryDirectory(prefix="tff-community-") as temp:
        temp_dir = Path(temp)
        copied = temp_dir / "example.tex"
        copied.write_text(entry["code"], encoding="utf-8")
        command = [
            latexmk,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-{entry['engine']}",
            "example.tex",
        ]
        env = dict(os.environ)
        env["TEXINPUTS"] = f"{source_dir.as_posix()}//:{env.get('TEXINPUTS', '')}"
        result = subprocess.run(
            command,
            cwd=temp_dir,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
            check=False,
        )
        return result.returncode == 0, result.stdout[-3000:]


def choose_compile_samples(entries: list[dict[str, Any]]) -> list[str]:
    preferred = (
        ("opentikz-content", "encoder-decoder"),
        ("janosh-diagrams", "self attention"),
        ("petarv-tikz", "self-attention"),
    )
    result: list[str] = []
    for source_id, needle in preferred:
        match = next(
            (
                item
                for item in entries
                if item["source_id"] == source_id
                and needle in (item["title"] + " " + item["source_locator"]["path"]).casefold()
                and item["compile_eligible"]
            ),
            None,
        )
        if match:
            result.append(match["id"])
    return result


def write_outputs(entries: list[dict[str, Any]], sources: list[dict[str, Any]], compile_samples: bool) -> None:
    sample_ids = choose_compile_samples(entries)
    if compile_samples:
        by_id = {item["id"]: item for item in entries}
        for sample_id in sample_ids:
            entry = by_id[sample_id]
            ok, output = compile_entry(entry)
            if ok:
                entry["compile_status"] = "passed"
                entry["verification"] = "source-compiled"
            elif output != "toolchain-unavailable":
                entry["compile_status"] = "failed"
                print(f"warning: compile failed for {sample_id}:\n{output}")

    CORPUS_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in entries),
        encoding="utf-8",
    )
    index = {
        "schema_version": "1.0",
        "kind": "source-example-corpus",
        "sources": [source["source_id"] for source in sources],
        "examples_file": OUTPUT.name,
        "total_examples": len(entries),
        "renderable_examples": sum(item["renderable"] for item in entries),
        "compile_eligible_examples": sum(item["compile_eligible"] for item in entries),
        "safety_flagged_examples": sum(bool(item["safety_flags"]) for item in entries),
        "source_counts": dict(sorted(Counter(item["source_id"] for item in entries).items())),
        "figure_families": dict(
            sorted(Counter(family for item in entries for family in item["figure_families"]).items())
        ),
        "compile_sample_ids": sample_ids,
        "compile_status": dict(sorted(Counter(item["compile_status"] for item in entries).items())),
        "verification": dict(sorted(Counter(item["verification"] for item in entries).items())),
    }
    INDEX.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    SOURCES_INDEX.write_text(
        json.dumps(runtime_sources_payload(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify(entries: list[dict[str, Any]], sources: list[dict[str, Any]]) -> None:
    validate_sources(sources)
    if not OUTPUT.is_file() or not INDEX.is_file():
        raise SystemExit("community corpus has not been built")
    committed = [
        json.loads(line)
        for line in OUTPUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(committed) != len(entries):
        raise SystemExit(
            f"community corpus count mismatch: expected={len(entries)} actual={len(committed)}"
        )
    expected = {
        item["id"]: (item["source_hash"], item["code_hash"])
        for item in entries
    }
    actual = {
        item["id"]: (item["source_hash"], item["code_hash"])
        for item in committed
    }
    if expected != actual:
        raise SystemExit("community corpus hashes do not match pinned sources")
    index = load_json(INDEX)
    if index["total_examples"] != len(entries):
        raise SystemExit("community index total_examples mismatch")
    print(
        "ok: community corpus "
        f"examples={len(entries)} renderable={sum(item['renderable'] for item in entries)} "
        f"safety_flagged={sum(bool(item['safety_flags']) for item in entries)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("--compile-samples", action="store_true")
    args = parser.parse_args()

    sources = community_sources()
    validate_sources(sources)
    entries = build_entries(sources)
    if args.action == "build":
        write_outputs(entries, sources, args.compile_samples)
        print(f"ok: wrote {len(entries)} community examples -> {OUTPUT}")
    else:
        verify(entries, sources)


if __name__ == "__main__":
    main()
