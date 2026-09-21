from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .io import load_json
from .manifest import utc_now, write_manifest
from .theme import load_profile


class QAError(RuntimeError):
    pass


def _pdf_info(pdf: Path) -> dict[str, Any]:
    if shutil.which("pdfinfo") is None:
        raise QAError("pdfinfo is required for figure inspection")
    result = subprocess.run(
        ["pdfinfo", str(pdf)], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise QAError(result.stderr.strip() or f"pdfinfo failed: {pdf}")
    pages_match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    size_match = re.search(
        r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        result.stdout, flags=re.MULTILINE,
    )
    pages = int(pages_match.group(1)) if pages_match else None
    width_pt = float(size_match.group(1)) if size_match else None
    height_pt = float(size_match.group(2)) if size_match else None
    pt_to_mm = 25.4 / 72.0
    return {
        "pages": pages,
        "width_pt": width_pt,
        "height_pt": height_pt,
        "width_mm": round(width_pt * pt_to_mm, 2) if width_pt is not None else None,
        "height_mm": round(height_pt * pt_to_mm, 2) if height_pt is not None else None,
    }


def _render_preview(pdf: Path, output: Path, dpi: int = 180) -> Path:
    if shutil.which("pdftoppm") is None:
        raise QAError("pdftoppm is required for figure inspection")
    output.parent.mkdir(parents=True, exist_ok=True)
    stem = output.with_suffix("")
    result = subprocess.run(
        ["pdftoppm", "-singlefile", "-png", "-r", str(int(dpi)), str(pdf), str(stem)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise QAError(result.stderr.strip() or f"pdftoppm failed: {pdf}")
    generated = stem.with_suffix(".png")
    if not generated.is_file():
        raise QAError(f"preview renderer did not create: {generated}")
    if generated != output:
        generated.replace(output)
    return output


def inspect_spec(spec: dict[str, Any], spec_path: Path, dpi: int = 180) -> dict[str, Any]:
    figure_dir = spec_path.parent
    basename = (spec.get("outputs") or {}).get("basename", "figure")
    pdf = figure_dir / f"{basename}.pdf"
    if not pdf.is_file():
        raise QAError(f"PDF does not exist; build the figure first: {pdf}")
    info = _pdf_info(pdf)
    warnings: list[str] = []
    if info.get("pages") != 1:
        warnings.append(f"expected a single-page figure PDF, got {info.get('pages')}")

    profile = None
    if spec.get("schema_version") == "1.1":
        profile_id = (spec.get("profile") or {}).get("id", "journal-single-column")
        profile = load_profile(profile_id)
        target = float(profile.get("target_width_mm", 0) or 0)
        width = info.get("width_mm")
        if target and width:
            if width > target * 1.2:
                warnings.append(
                    f"natural PDF width {width:.1f} mm exceeds profile target {target:.1f} mm by more than 20%; inspect readability after journal scaling"
                )
            elif width < target * 0.35:
                warnings.append(
                    f"natural PDF width {width:.1f} mm is much smaller than profile target {target:.1f} mm; inspect line/text scale"
                )

    preview = figure_dir / ".funfig" / "preview.png"
    _render_preview(pdf, preview, dpi=dpi)

    manifest_file = figure_dir / ".funfig" / "manifest.json"
    if not manifest_file.is_file():
        raise QAError(f"manifest does not exist: {manifest_file}")
    manifest = load_json(manifest_file)
    manifest["qa"] = {
        "status": "preview_ready",
        "machine_checks_passed": not warnings,
        "visual_review": "pending",
        "warnings": warnings,
        "pdf": info,
        "preview": ".funfig/preview.png",
        "preview_dpi": int(dpi),
        "checked_at": utc_now(),
    }
    if profile:
        manifest["qa"]["profile"] = {
            "id": profile["id"],
            "target_width_mm": profile.get("target_width_mm"),
            "minimum_text_pt": profile.get("minimum_text_pt"),
        }
    write_manifest(figure_dir, manifest)
    return manifest["qa"]


def mark_visual_review(spec_path: Path, passed: bool, note: str) -> dict[str, Any]:
    figure_dir = spec_path.parent
    manifest_file = figure_dir / ".funfig" / "manifest.json"
    if not manifest_file.is_file():
        raise QAError(f"manifest does not exist: {manifest_file}")
    manifest = load_json(manifest_file)
    qa = manifest.setdefault("qa", {})
    if qa.get("status") not in {"preview_ready", "passed", "failed"}:
        raise QAError("run 'funfig inspect' before recording a visual review")
    qa["visual_review"] = "passed" if passed else "failed"
    qa["status"] = "passed" if passed and qa.get("machine_checks_passed", True) else "failed"
    qa["review_note"] = note
    qa["reviewed_at"] = utc_now()
    write_manifest(figure_dir, manifest)
    return qa
