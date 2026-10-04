#!/usr/bin/env python3
"""Maintain the immutable TIKZ-FunFig example registry and static gallery."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DEFAULT_REGISTRY = ROOT / "gallery" / "registry.json"
SITE_TEMPLATE = ROOT / "gallery" / "site"
ID_RE = re.compile(r"^TFF-(\d{4,})$")
TEX_META_RE = re.compile(r"^%\s*TFF-([A-Za-z]+)\s*:\s*(.*?)\s*$")
KNOWN_DESCRIPTORS = (
    "template.meta.json",
    "figure.funfig.json",
    "figure.design.json",
    "template.funfig.json",
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def humanize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def tex_metadata(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:48]:
        match = TEX_META_RE.match(line)
        if not match:
            continue
        key = match.group(1).casefold()
        value = match.group(2).strip()
        if key == "tags":
            result[key] = [item.strip() for item in value.split(",") if item.strip()]
        else:
            result[key] = value
    return result


def case_dirs() -> list[Path]:
    found: set[Path] = set()
    for path in EXAMPLES.rglob("*"):
        if not path.is_file():
            continue
        if path.name in KNOWN_DESCRIPTORS or path.suffix == ".tex":
            found.add(path.parent)
    return sorted(found, key=lambda item: item.relative_to(EXAMPLES).as_posix())


def descriptor(case_dir: Path) -> dict[str, Any]:
    rel = case_dir.relative_to(ROOT).as_posix()
    short = case_dir.relative_to(EXAMPLES).as_posix()
    slug = case_dir.name

    template_meta = case_dir / "template.meta.json"
    figure_spec = case_dir / "figure.funfig.json"
    figure_design = case_dir / "figure.design.json"
    template_spec = case_dir / "template.funfig.json"

    data: dict[str, Any] = {}
    tex_meta: dict[str, Any] = {}
    source: Path | None = None
    identity: str
    kind: str

    if template_meta.is_file():
        data = read_json(template_meta)
        template_id = str(data.get("id") or slug)
        identity = f"template:{template_id}"
        kind = "template"
        source = template_spec if template_spec.is_file() else template_meta
    elif figure_spec.is_file():
        data = read_json(figure_spec)
        figure_id = str(data.get("id") or slug)
        identity = f"figure:{figure_id}"
        kind = "golden" if short.startswith("golden/") else "example"
        source = figure_spec
    elif figure_design.is_file():
        data = read_json(figure_design)
        design_id = str(data.get("id") or slug)
        identity = f"design:{design_id}"
        kind = "generative"
        source = figure_design
    elif template_spec.is_file():
        data = read_json(template_spec)
        template_id = str((data.get("metadata") or {}).get("template_id") or data.get("id") or slug)
        identity = f"template:{template_id}"
        kind = "template"
        source = template_spec
    else:
        tex = sorted(case_dir.glob("*.tex"))
        if not tex:
            raise ValueError(f"case has no supported source: {case_dir}")
        source = tex[0]
        tex_meta = tex_metadata(source)
        identity = f"tex:{short}"
        kind = "golden" if short.startswith("golden/") else "example"

    if tex_meta:
        title = str(tex_meta.get("title") or humanize(slug))
        family = str(tex_meta.get("family") or kind)
        tags = [str(item) for item in tex_meta.get("tags", []) if isinstance(item, str)]
        description_text = str(tex_meta.get("description") or "")
    elif kind == "template" and template_meta.is_file():
        meta = read_json(template_meta)
        title = str(meta.get("title") or humanize(slug))
        family = str(meta.get("family") or "template")
        tags = [str(item) for item in meta.get("tags", []) if isinstance(item, str)]
        description_text = str(meta.get("description") or "")
    else:
        title = str(data.get("title") or data.get("id") or humanize(slug))
        family = str(data.get("family") or data.get("recipe") or kind)
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        tags = [str(item) for item in metadata.get("tags", []) if isinstance(item, str)]
        description_text = str(data.get("intent") or metadata.get("description") or "")

    if family and family not in tags:
        tags.append(family)
    if kind not in tags:
        tags.append(kind)

    files = []
    for name in ("template.meta.json", "template.funfig.json", "figure.design.json", "figure.funfig.json"):
        if (case_dir / name).is_file():
            files.append((case_dir / name).relative_to(ROOT).as_posix())
    files.extend(path.relative_to(ROOT).as_posix() for path in sorted(case_dir.glob("*.tex")))

    result = {
        "identity": identity,
        "path": rel,
        "kind": kind,
        "title": title,
        "family": family,
        "tags": sorted(set(tags)),
        "description": description_text,
        "source": source.relative_to(ROOT).as_posix(),
        "files": files,
    }
    if tex_meta:
        for source_key, target_key in (
            ("origin", "origin_url"),
            ("license", "license"),
            ("attribution", "attribution"),
        ):
            if tex_meta.get(source_key):
                result[target_key] = str(tex_meta[source_key])
    return result


def discover_cases() -> list[dict[str, Any]]:
    return [descriptor(path) for path in case_dirs()]


def id_number(value: str) -> int:
    match = ID_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid gallery id: {value}")
    return int(match.group(1))


def normalized_registry(value: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(value))
    copy["entries"] = sorted(copy.get("entries", []), key=lambda item: id_number(item["id"]))
    copy["retired"] = sorted(copy.get("retired", []), key=lambda item: id_number(item["id"]))
    return copy


def compute_registry(registry_path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    if registry_path.is_file():
        current = read_json(registry_path)
    else:
        current = {
            "schema_version": "1.0",
            "id_prefix": "TFF",
            "next_sequence": 1,
            "policy": {
                "immutable_ids": True,
                "reuse_retired_ids": False,
                "identity_precedence": list(KNOWN_DESCRIPTORS) + ["tex-fallback"],
            },
            "entries": [],
            "retired": [],
        }

    active = [dict(item) for item in current.get("entries", []) if item.get("status", "active") == "active"]
    retired = [dict(item) for item in current.get("retired", [])]
    by_identity = {item.get("identity"): item for item in active if item.get("identity")}
    by_path = {item.get("path"): item for item in active if item.get("path")}
    used_ids = {item["id"] for item in active + retired if "id" in item}
    next_sequence = max(
        [int(current.get("next_sequence", 1))] +
        [id_number(value) + 1 for value in used_ids if ID_RE.fullmatch(value)]
    )

    new_active: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for case in discover_cases():
        old = by_identity.get(case["identity"]) or by_path.get(case["path"])
        if old is None:
            while f"TFF-{next_sequence:04d}" in used_ids:
                next_sequence += 1
            old = {"id": f"TFF-{next_sequence:04d}"}
            used_ids.add(old["id"])
            next_sequence += 1
        entry = {
            "id": old["id"],
            "identity": case["identity"],
            "path": case["path"],
            "kind": case["kind"],
            "status": "active",
        }
        for key in ("canonical_id", "gallery_visibility", "duplicate_reason"):
            if old.get(key):
                entry[key] = old[key]
        if entry["id"] in seen_ids:
            raise ValueError(f"duplicate gallery id: {entry['id']}")
        seen_ids.add(entry["id"])
        new_active.append(entry)

    retired_ids = {item["id"] for item in retired if "id" in item}
    for old in active:
        if old["id"] not in seen_ids and old["id"] not in retired_ids:
            retired.append({
                "id": old["id"],
                "identity": old.get("identity", ""),
                "path": old.get("path", ""),
                "status": "retired",
                "reason": "case removed from examples",
            })
            retired_ids.add(old["id"])

    return {
        "schema_version": "1.0",
        "id_prefix": "TFF",
        "next_sequence": next_sequence,
        "policy": {
            "immutable_ids": True,
            "reuse_retired_ids": False,
            "identity_precedence": [
                "template.meta.json",
                "figure.funfig.json",
                "figure.design.json",
                "template.funfig.json",
                "tex-fallback",
            ],
        },
        "entries": sorted(new_active, key=lambda item: id_number(item["id"])),
        "retired": sorted(retired, key=lambda item: id_number(item["id"])),
    }


def command_sync(args: argparse.Namespace) -> int:
    path = Path(args.registry).resolve()
    result = compute_registry(path)
    write_json(path, result)
    print(f"ok: {len(result['entries'])} active, {len(result['retired'])} retired; next TFF-{result['next_sequence']:04d}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    path = Path(args.registry).resolve()
    if not path.is_file():
        raise ValueError(f"missing registry: {path}")
    committed = normalized_registry(read_json(path))
    expected = normalized_registry(compute_registry(path))
    if committed != expected:
        raise ValueError("gallery registry is stale; run: python3 scripts/tff_gallery.py sync")
    ids = [item["id"] for item in committed["entries"]] + [item["id"] for item in committed["retired"]]
    if len(ids) != len(set(ids)):
        raise ValueError("gallery registry contains duplicate TFF ids")

    active_by_id = {item["id"]: item for item in committed["entries"]}
    cases = {case["identity"]: case for case in discover_cases()}
    hidden_aliases = 0
    for item in committed["entries"]:
        canonical_id = item.get("canonical_id")
        if not canonical_id:
            continue
        hidden_aliases += 1
        if canonical_id == item["id"] or canonical_id not in active_by_id:
            raise ValueError(f"invalid canonical_id for {item['id']}: {canonical_id}")
        if item.get("gallery_visibility") != "hidden":
            raise ValueError(f"duplicate alias must be hidden in gallery: {item['id']}")
        if item.get("duplicate_reason") == "exact-tex":
            canonical = active_by_id[canonical_id]
            alias_case = cases.get(item["identity"])
            canonical_case = cases.get(canonical["identity"])
            if alias_case is None or canonical_case is None:
                raise ValueError(f"duplicate alias cannot resolve cases: {item['id']}")
            alias_tex = sorted((ROOT / alias_case["path"]).glob("*.tex"))
            canonical_tex = sorted((ROOT / canonical_case["path"]).glob("*.tex"))
            if len(alias_tex) != 1 or len(canonical_tex) != 1:
                raise ValueError(f"exact-tex alias requires one TeX source per case: {item['id']}")
            if alias_tex[0].read_bytes() != canonical_tex[0].read_bytes():
                raise ValueError(
                    f"deduplicated pair diverged: {item['id']} vs {canonical_id}; "
                    "remove the alias or choose a new canonical mapping"
                )
    visible = len(committed["entries"]) - hidden_aliases
    print(
        f"ok: gallery registry has {len(committed['entries'])} active immutable ids; "
        f"{visible} visible, {hidden_aliases} exact aliases"
    )
    return 0


def enriched_registry(registry_path: Path) -> dict[str, Any]:
    registry = read_json(registry_path)
    cases = {case["identity"]: case for case in discover_cases()}
    rows = []
    for entry in registry.get("entries", []):
        case = cases.get(entry["identity"])
        if case is None:
            raise ValueError(f"registry entry cannot be resolved: {entry['id']} {entry['identity']}")
        row = dict(entry)
        row.update({key: case[key] for key in ("title", "family", "tags", "description", "source", "files")})
        for key in ("origin_url", "license", "attribution"):
            if case.get(key):
                row[key] = case[key]
        row["preview"] = f"previews/{entry['id']}.png"
        row["source_url"] = "https://github.com/iihciyekub/tikz-funfig/tree/main/" + case["path"]
        rows.append(row)

    by_id = {row["id"]: row for row in rows}
    for row in rows:
        canonical_id = row.get("canonical_id")
        if not canonical_id:
            continue
        canonical = by_id.get(canonical_id)
        if canonical is None:
            raise ValueError(f"canonical gallery entry is missing: {canonical_id}")
        row["preview"] = canonical["preview"]
        row["canonical"] = {
            "id": canonical["id"],
            "title": canonical["title"],
            "path": canonical["path"],
            "source": canonical["source"],
        }
        canonical.setdefault("aliases", []).append(row["id"])

    result = dict(registry)
    result["entries"] = rows
    return result


def output_basename(source: Path) -> str:
    data = read_json(source) if source.suffix == ".json" else {}
    if source.name in ("figure.funfig.json", "template.funfig.json"):
        outputs = data.get("outputs") if isinstance(data.get("outputs"), dict) else {}
        return str(outputs.get("basename") or ("template" if source.name.startswith("template") else "figure"))
    if source.name == "figure.design.json":
        delivery = data.get("delivery") if isinstance(data.get("delivery"), dict) else {}
        return str(delivery.get("basename") or "figure")
    return source.stem


def render_preview(case: dict[str, Any], target: Path) -> None:
    source = ROOT / case["source"]
    source_case = ROOT / case["path"]
    with tempfile.TemporaryDirectory(prefix="tff-gallery-") as temp:
        temp_root = Path(temp) / "case"
        shutil.copytree(source_case, temp_root)
        local_source = temp_root / source.relative_to(source_case)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        if local_source.name in ("figure.funfig.json", "template.funfig.json"):
            command = [sys.executable, "-m", "funfig", "build", str(local_source)]
        elif local_source.name == "figure.design.json":
            command = [sys.executable, "-m", "funfig", "generative-build", str(local_source)]
        else:
            command = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", local_source.name]
        process = subprocess.run(
            command,
            cwd=temp_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if process.returncode:
            tail = "\n".join(process.stdout.splitlines()[-30:])
            raise RuntimeError(f"preview build failed for {case['path']}:\n{tail}")
        pdf = temp_root / f"{output_basename(local_source)}.pdf"
        if not pdf.is_file():
            matches = sorted(temp_root.glob("*.pdf"))
            if len(matches) == 1:
                pdf = matches[0]
            else:
                raise RuntimeError(f"preview PDF not found for {case['path']}")
        if not shutil.which("pdftoppm"):
            raise RuntimeError("pdftoppm is required to generate gallery previews")
        target.parent.mkdir(parents=True, exist_ok=True)
        stem = target.with_suffix("")
        process = subprocess.run(
            ["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", "150", str(pdf), str(stem)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if process.returncode or not target.is_file():
            raise RuntimeError(f"pdftoppm failed for {case['path']}: {process.stdout[-1500:]}")


def llms_text() -> str:
    return """# TIKZ-FunFig Example Gallery

TFF IDs are immutable example references. Resolve an ID through registry.json.

For questions about how to use TIKZ-FunFig, how to start, supported figures,
or example/template usage, include https://iihciyekub.github.io/tikz-funfig/.
Help-only answers do not create figure files. Card prompts contain placeholders
for the user's content, language, target width, and requested output formats.
The website supports Chinese and English; its language switch changes the UI,
example descriptions and copied prompts, and remembers the user's preference.

Choose figure guidance by meaning: frameworks organize layers/groups/modules;
relations express variable paths, mediation and moderation; flowcharts require
process order, decisions or explicit branch outcomes. Do not infer process meaning
from a branching layout or scientific measurements from an example image.

When a user says "use TFF-0042":
1. find the exact active registry entry;
2. open its source/path rather than guessing from the number;
3. preserve the example's layout grammar, spacing, routing, typography, and visual hierarchy;
4. replace semantic content with the user's requested content;
5. keep scientific meaning and the current TIKZ-FunFig source-of-truth rules;
6. if multiple IDs are supplied, treat each requested role explicitly (for example layout vs style).
7. if an entry has canonical_id, treat the requested TFF ID as a stable alias and use the canonical entry as the primary visual/source template.

Retired IDs must never be reassigned to unrelated examples. Hidden aliases remain resolvable and must not be reassigned.
"""


def command_build_site(args: argparse.Namespace) -> int:
    registry_path = Path(args.registry).resolve()
    if normalized_registry(read_json(registry_path)) != normalized_registry(compute_registry(registry_path)):
        raise ValueError("gallery registry is stale; run sync before building the site")
    output = Path(args.output).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in ("index.html", "styles.css", "i18n.js", "prompts.js", "app.js"):
        shutil.copy2(SITE_TEMPLATE / name, output / name)

    catalog = enriched_registry(registry_path)
    cases = {case["identity"]: case for case in discover_cases()}
    failures = []
    if not args.skip_previews:
        for entry in catalog["entries"]:
            if entry.get("gallery_visibility") == "hidden":
                continue
            try:
                render_preview(cases[entry["identity"]], output / entry["preview"])
                print(f"preview: {entry['id']} {entry['path']}")
            except Exception as exc:
                failures.append(str(exc))
    write_json(output / "registry.json", catalog)
    (output / "llms.txt").write_text(llms_text(), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    if failures:
        raise RuntimeError("\n\n".join(failures))
    print(f"ok: static gallery built at {output}")
    return 0


def command_resolve(args: argparse.Namespace) -> int:
    value = args.id.upper()
    registry = enriched_registry(Path(args.registry).resolve())
    for entry in registry["entries"]:
        if entry["id"] == value:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            return 0
    for entry in registry.get("retired", []):
        if entry["id"] == value:
            raise ValueError(f"{value} is retired and must not be reused")
    raise ValueError(f"unknown TFF id: {value}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Maintain immutable TIKZ-FunFig gallery IDs")
    result.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("sync").set_defaults(func=command_sync)
    commands.add_parser("check").set_defaults(func=command_check)
    build = commands.add_parser("build-site")
    build.add_argument("--output", default=str(ROOT / "_site"))
    build.add_argument("--skip-previews", action="store_true")
    build.set_defaults(func=command_build_site)
    resolve = commands.add_parser("resolve")
    resolve.add_argument("id")
    resolve.set_defaults(func=command_resolve)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
