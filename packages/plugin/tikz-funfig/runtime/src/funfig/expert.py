from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .knowledge import all_entries
from .manifest import utc_now
from .qa import _pdf_info, _render_preview


class ExpertBuildError(RuntimeError):
    pass


DANGEROUS_TEX = (r"\write18", r"\ShellEscape", r"\input|", r"\immediate\write18")


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
    for suffix in ("aux", "fdb_latexmk", "fls", "log", "out", "synctex.gz"):
        candidate = tex.with_suffix("." + suffix)
        if candidate.exists():
            destination = build_dir / candidate.name
            destination.unlink(missing_ok=True)
            shutil.move(str(candidate), str(destination))


def build_expert(
    tex_path: str | Path,
    *,
    sources: list[str],
    cards: list[str] | None = None,
    engine: str = "auto",
) -> tuple[Path, Path]:
    tex = Path(tex_path).resolve()
    if not tex.is_file():
        raise ExpertBuildError(f"expert TeX source does not exist: {tex}")
    if not sources:
        raise ExpertBuildError("Expert TikZ Mode requires at least one --source reference")
    cards = list(cards or [])
    _validate_knowledge_refs(list(sources), cards)
    text = tex.read_text(encoding="utf-8")
    found = [token for token in DANGEROUS_TEX if token in text]
    if found:
        raise ExpertBuildError(
            "Expert TikZ source contains shell/input execution syntax that is not allowed by this mode: "
            + ", ".join(found)
        )
    if shutil.which("latexmk") is None:
        raise ExpertBuildError("latexmk is required for Expert TikZ Mode")
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
    pdf_info = _pdf_info(pdf)
    _render_preview(pdf, preview, dpi=180)
    qa_warnings: list[str] = []
    if pdf_info.get("pages") != 1:
        qa_warnings.append(f"expected a single-page figure PDF, got {pdf_info.get('pages')}")

    manifest = {
        "manifest_version": "1.0",
        "mode": "raw-expert",
        "status": "built",
        "qa": {
            "status": "preview_ready",
            "machine_checks_passed": not qa_warnings,
            "visual_review": "pending",
            "warnings": qa_warnings,
            "pdf": pdf_info,
            "preview": ".funfig/expert-preview.png",
            "preview_dpi": 180,
        },
        "sources": list(sources),
        "knowledge_cards": cards,
        "build": {"engine": selected, "command": command, "returncode": 0},
        "artifacts": {"tex": tex.name, "pdf": pdf.name, "log": ".funfig/expert-build/funfig-expert-build.log"},
        "hashes": {"tex_sha256": _sha256(tex), "pdf_sha256": _sha256(pdf)},
        "updated_at": utc_now(),
    }
    manifest_path = state_dir / "expert-manifest.json"
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
    qa["visual_review"] = "passed" if passed else "failed"
    qa["status"] = "passed" if passed and qa.get("machine_checks_passed", True) else "failed"
    qa["review_note"] = note
    qa["reviewed_at"] = utc_now()
    manifest["updated_at"] = utc_now()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return qa
