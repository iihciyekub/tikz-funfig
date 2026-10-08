from __future__ import annotations

import hashlib
import math
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .knowledge import all_entries
from .manifest import utc_now
from .qa import _pdf_info, _render_preview, analyze_pdf
from .design import validate_design


class ExpertBuildError(RuntimeError):
    pass


DANGEROUS_TEX = (r"\write18", r"\ShellEscape", r"\input|", r"\immediate\write18")
PACKAGE_RE = re.compile(r"\\(?:usepackage|RequirePackage)(?:\[[^\]]*\])?\{([^}]+)\}")
DOCUMENT_CLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _engine(tex: Path, configured: str) -> str:
    if configured != "auto":
        return configured
    text = tex.read_text(encoding="utf-8")
    return "xelatex" if any(ord(char) > 127 for char in text) else "pdflatex"


def _strip_tex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        kept: list[str] = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            kept.append(char)
            if char == "\\":
                escaped = not escaped
            else:
                escaped = False
        lines.append("".join(kept))
    return "\n".join(lines)


def _tex_resource_lookup(tex: Path, filename: str, kpsewhich: str) -> dict[str, Any]:
    local = tex.parent / filename
    if local.is_file():
        return {"file": filename, "available": True, "resolved": str(local), "source": "local"}
    process = subprocess.run(
        [kpsewhich, filename],
        cwd=tex.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    resolved = process.stdout.strip()
    return {
        "file": filename,
        "available": process.returncode == 0 and bool(resolved),
        "resolved": resolved or None,
        "source": "texmf" if resolved else None,
    }


def inspect_expert_dependencies(tex_path: str | Path) -> dict[str, Any]:
    tex = Path(tex_path).resolve()
    if not tex.is_file():
        raise ExpertBuildError(f"expert TeX source does not exist: {tex}")
    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich is None:
        raise ExpertBuildError("kpsewhich is required to inspect Expert TikZ dependencies")
    text = _strip_tex_comments(tex.read_text(encoding="utf-8"))
    class_match = DOCUMENT_CLASS_RE.search(text)
    document_class: dict[str, Any] | None = None
    if class_match:
        class_name = class_match.group(1).strip()
        document_class = {
            "name": class_name,
            **_tex_resource_lookup(tex, f"{class_name}.cls", kpsewhich),
        }
    package_names: list[str] = []
    for match in PACKAGE_RE.finditer(text):
        for raw in match.group(1).split(","):
            name = raw.strip()
            if name and name not in package_names:
                package_names.append(name)
    packages = [
        {"name": name, **_tex_resource_lookup(tex, f"{name}.sty", kpsewhich)}
        for name in package_names
    ]
    missing: list[str] = []
    if document_class and not document_class["available"]:
        missing.append(document_class["file"])
    missing.extend(item["file"] for item in packages if not item["available"])
    return {
        "document_class": document_class,
        "packages": packages,
        "missing": missing,
        "ok": not missing,
    }


def _validate_knowledge_refs(sources: list[str], cards: list[str]) -> None:
    entries = all_entries()
    source_ids = {item["id"] for item in entries if item["kind"] == "manual"}
    card_ids = {item["id"] for item in entries if item["kind"] == "card"}
    unknown_sources = sorted(set(sources) - source_ids)
    unknown_cards = sorted(set(cards) - card_ids)
    if unknown_sources:
        raise ExpertBuildError("unknown official/manual source ID(s): " + ", ".join(unknown_sources))
    if unknown_cards:
        raise ExpertBuildError("unknown knowledge card ID(s): " + ", ".join(unknown_cards))


def _relocate_intermediates(tex: Path, state_dir: Path) -> None:
    build_dir = state_dir / "expert-build"
    build_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("aux", "fdb_latexmk", "fls", "log", "out", "synctex.gz", "ffgeom"):
        candidate = tex.with_suffix("." + suffix)
        if candidate.exists():
            destination = build_dir / candidate.name
            destination.unlink(missing_ok=True)
            shutil.move(str(candidate), str(destination))


def build_expert(
    tex_path: str | Path,
    *,
    sources: list[str] | None = None,
    cards: list[str] | None = None,
    engine: str = "auto",
    target_width_mm: float | None = None,
    minimum_text_pt: float | None = None,
) -> tuple[Path, Path]:
    tex = Path(tex_path).resolve()
    if not tex.is_file():
        raise ExpertBuildError(f"expert TeX source does not exist: {tex}")
    design_path = tex.parent / 'figure.design.json'
    appearance = {}
    if design_path.is_file():
        design = validate_design(design_path)
        if design['render_mode'] == 'expert' and design['delivery']['basename'] == tex.stem:
            appearance = design['appearance']
    target_width_mm = target_width_mm if target_width_mm is not None else appearance.get('target_width_mm', 178.0)
    minimum_text_pt = minimum_text_pt if minimum_text_pt is not None else appearance.get('minimum_text_pt', 7.5)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in (target_width_mm, minimum_text_pt)):
        raise ExpertBuildError('Expert width and text baseline must be finite positive numbers')
    sources = list(sources or [])
    cards = list(cards or [])
    if not sources and not cards:
        raise ExpertBuildError("Expert TikZ Mode requires at least one trusted --source or --card reference")
    _validate_knowledge_refs(sources, cards)
    text = tex.read_text(encoding="utf-8")
    found = [token for token in DANGEROUS_TEX if token in text]
    if found:
        raise ExpertBuildError(
            "Expert TikZ source contains shell/input execution syntax that is not allowed by this mode: "
            + ", ".join(found)
        )
    if shutil.which("latexmk") is None:
        raise ExpertBuildError("latexmk is required for Expert TikZ Mode")
    dependencies = inspect_expert_dependencies(tex)
    if dependencies["missing"]:
        raise ExpertBuildError(
            "missing TeX dependency resource(s): " + ", ".join(dependencies["missing"])
            + ". Install the required TeX package(s) before expert-build."
        )
    selected = _engine(tex, engine)
    if selected not in {"pdflatex", "xelatex", "lualatex"}:
        raise ExpertBuildError(f"unsupported TeX engine: {selected}")
    if shutil.which(selected) is None:
        raise ExpertBuildError(f"TeX engine is not available: {selected}")

    command = ["latexmk", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error"]
    command.append({"pdflatex": "-pdf", "xelatex": "-xelatex", "lualatex": "-lualatex"}[selected])
    command.append(tex.name)
    process = subprocess.run(
        command, cwd=tex.parent, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    state_dir = tex.parent / ".funfig"
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / "expert-manifest.json"
    previous_manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            previous_manifest = {}
    previous_qa = previous_manifest.get("qa") or {}
    review_history = list(previous_qa.get("review_history") or [])
    build_iteration = int(previous_manifest.get("build_iteration") or 0) + 1
    build_dir = state_dir / "expert-build"
    build_dir.mkdir(parents=True, exist_ok=True)
    log = build_dir / "funfig-expert-build.log"
    log.write_text(process.stdout, encoding="utf-8")
    _relocate_intermediates(tex, state_dir)
    if process.returncode:
        raise ExpertBuildError(
            f"Expert TikZ compile failed; see {log}\n" + "\n".join(process.stdout.splitlines()[-30:])
        )
    pdf = tex.with_suffix(".pdf")
    if not pdf.is_file():
        raise ExpertBuildError(f"compile succeeded but PDF was not created: {pdf}")

    preview = state_dir / "expert-preview.png"
    checks = analyze_pdf(pdf, target_width_mm=target_width_mm, minimum_text_pt=minimum_text_pt,
                         target_source='expert-output-profile')
    pdf_info = checks['pdf']
    _render_preview(pdf, preview, dpi=180)
    qa_warnings = checks['warnings']

    manifest = {
        "manifest_version": "1.0",
        "mode": "raw-expert",
        "status": "built",
        "qa": {
            "status": "preview_ready",
            "machine_checks_passed": not qa_warnings,
            "visual_review": "pending",
            "warnings": qa_warnings,
            "defects": checks['defects'],
            "text_metrics": checks['text_metrics'],
            "size_check": checks['size_check'],
            "publication_projection": checks['publication_projection'],
            "pdf": pdf_info,
            "preview": ".funfig/expert-preview.png",
            "preview_dpi": 180,
            "review_history": review_history,
            "review_count": len(review_history),
            "repair_cycles": sum(1 for item in review_history if item.get("result") == "failed"),
        },
        "build_iteration": build_iteration,
        "sources": sources,
        "knowledge_cards": cards,
        "build": {
            "engine": selected,
            "command": command,
            "returncode": 0,
            "dependencies": dependencies,
        },
        "artifacts": {"tex": tex.name, "pdf": pdf.name, "log": ".funfig/expert-build/funfig-expert-build.log"},
        "hashes": {"tex_sha256": _sha256(tex), "pdf_sha256": _sha256(pdf)},
        "updated_at": utc_now(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return pdf, manifest_path


def mark_expert_visual_review(tex_path: str | Path, passed: bool, note: str) -> dict[str, Any]:
    tex = Path(tex_path).resolve()
    manifest_path = tex.parent / ".funfig" / "expert-manifest.json"
    if not manifest_path.is_file():
        raise ExpertBuildError(f"expert manifest does not exist: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("mode") != "raw-expert":
        raise ExpertBuildError("manifest is not an Expert TikZ Mode build")
    qa = manifest.setdefault("qa", {})
    if qa.get("status") not in {"preview_ready", "passed", "failed"}:
        raise ExpertBuildError("expert-build must create a preview before visual review can be recorded")
    reviewed_at = utc_now()
    result = "passed" if passed else "failed"
    qa["visual_review"] = result
    qa["status"] = "passed" if passed and qa.get("machine_checks_passed", True) else "failed"
    qa["review_note"] = note
    qa["reviewed_at"] = reviewed_at
    history = qa.setdefault("review_history", [])
    history.append({
        "build_iteration": int(manifest.get("build_iteration") or 1),
        "result": result,
        "note": note,
        "reviewed_at": reviewed_at,
        "tex_sha256": (manifest.get("hashes") or {}).get("tex_sha256"),
    })
    qa["review_count"] = len(history)
    qa["repair_cycles"] = sum(1 for item in history if item.get("result") == "failed")
    manifest["updated_at"] = utc_now()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return qa
