from __future__ import annotations

import json
import html
import re
import shutil
import statistics
import subprocess
from pathlib import Path
from typing import Any

from .io import load_json
from .manifest import utc_now, write_manifest
from .theme import load_profile


class QAError(RuntimeError):
    pass


_TEX_LENGTH_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)(pt|mm|cm|in)\s*$")


def _tex_length_mm(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    match = _TEX_LENGTH_RE.match(value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    factor = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72.27}[unit]
    return number * factor


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


def _pdf_text_metrics(pdf: Path) -> dict[str, Any] | None:
    if shutil.which("pdftotext") is None:
        return None
    result = subprocess.run(
        ["pdftotext", "-bbox", str(pdf), "-"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        return None
    heights: list[float] = []
    words: list[dict[str, Any]] = []
    pattern = re.compile(
        r'<word\s+[^>]*?yMin="([0-9.]+)"[^>]*?yMax="([0-9.]+)"',
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(result.stdout):
        y_min = float(match.group(1))
        y_max = float(match.group(2))
        height = y_max - y_min
        if 1.0 <= height <= 100.0:
            heights.append(height)
    word_pattern = re.compile(
        r'<word\s+[^>]*?xMin="([0-9.]+)"[^>]*?yMin="([0-9.]+)"'
        r'[^>]*?xMax="([0-9.]+)"[^>]*?yMax="([0-9.]+)"[^>]*>(.*?)</word>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in word_pattern.finditer(result.stdout):
        words.append(
            {
                "text": html.unescape(re.sub(r"<[^>]+>", "", match.group(5))).strip(),
                "x_min": float(match.group(1)),
                "y_min": float(match.group(2)),
                "x_max": float(match.group(3)),
                "y_max": float(match.group(4)),
            }
        )

    overlaps: list[dict[str, Any]] = []
    for index, left in enumerate(words):
        for right in words[index + 1:]:
            overlap_x = min(left["x_max"], right["x_max"]) - max(left["x_min"], right["x_min"])
            overlap_y = min(left["y_max"], right["y_max"]) - max(left["y_min"], right["y_min"])
            if overlap_x <= 0.75 or overlap_y <= 0.75:
                continue
            overlaps.append(
                {
                    "left": left["text"],
                    "right": right["text"],
                    "overlap_x_pt": round(overlap_x, 2),
                    "overlap_y_pt": round(overlap_y, 2),
                }
            )

    if not heights:
        return {
            "word_count": 0,
            "bbox_height_pt": None,
            "bbox_overlap_count": len(overlaps),
            "bbox_overlaps": overlaps[:12],
        }
    heights.sort()
    p10_index = max(0, min(len(heights) - 1, round((len(heights) - 1) * 0.10)))
    return {
        "word_count": len(heights),
        "bbox_height_pt": {
            "min": round(heights[0], 2),
            "p10": round(heights[p10_index], 2),
            "median": round(float(statistics.median(heights)), 2),
            "max": round(heights[-1], 2),
        },
        "bbox_overlap_count": len(overlaps),
        "bbox_overlaps": overlaps[:12],
    }


def inspect_spec(spec: dict[str, Any], spec_path: Path, dpi: int = 180) -> dict[str, Any]:
    figure_dir = spec_path.parent
    basename = (spec.get("outputs") or {}).get("basename", "figure")
    pdf = figure_dir / f"{basename}.pdf"
    if not pdf.is_file():
        raise QAError(f"PDF does not exist; build the figure first: {pdf}")
    info = _pdf_info(pdf)
    text_metrics = _pdf_text_metrics(pdf)
    warnings: list[str] = []
    if info.get("pages") != 1:
        warnings.append(f"expected a single-page figure PDF, got {info.get('pages')}")
    overlap_count = int((text_metrics or {}).get("bbox_overlap_count") or 0)
    if overlap_count:
        examples = (text_metrics or {}).get("bbox_overlaps") or []
        sample = ""
        if examples:
            first = examples[0]
            sample = f" (for example: {first['left']!r} overlaps {first['right']!r})"
        warnings.append(
            f"detected {overlap_count} overlapping text bounding-box pair(s){sample}; "
            "increase node clearance or repair routing/layout before visual review"
        )

    profile = None
    publication_scale = 1.0
    projected_size: dict[str, float] | None = None
    target_width_mm: float | None = None
    minimum_text_pt = 0.0
    target_source: str | None = None
    if spec.get("schema_version") == "1.1":
        profile_id = (spec.get("profile") or {}).get("id", "journal-single-column")
        profile = load_profile(profile_id)
        target_width_mm = float(profile.get("target_width_mm", 0) or 0) or None
        minimum_text_pt = float(profile.get("minimum_text_pt", 0) or 0)
        target_source = f"profile:{profile_id}"
    else:
        target_width_mm = _tex_length_mm((spec.get("canvas") or {}).get("width"))
        if target_width_mm:
            # Legacy/plot FigureSpec has no Publication Profile. Use the explicit
            # canvas width as the intended physical width and the project's
            # conservative journal baseline for text-risk projection.
            minimum_text_pt = 7.5
            target_source = "canvas.width"

    width = info.get("width_mm")
    if target_width_mm and width:
        publication_scale = min(1.0, target_width_mm / float(width))
        projected_size = {
            "width_mm": round(float(width) * publication_scale, 2),
            "height_mm": round(float(info.get("height_mm") or 0) * publication_scale, 2),
            "scale": round(publication_scale, 4),
        }
        if width > target_width_mm * 1.2:
            warnings.append(
                f"natural PDF width {width:.1f} mm exceeds target {target_width_mm:.1f} mm by more than 20%; inspect readability after publication scaling"
            )
        elif width < target_width_mm * 0.35:
            warnings.append(
                f"natural PDF width {width:.1f} mm is much smaller than target {target_width_mm:.1f} mm; inspect line/text scale"
            )

        bbox = (text_metrics or {}).get("bbox_height_pt") or {}
        median_height = bbox.get("median")
        p10_height = bbox.get("p10")
        if minimum_text_pt and publication_scale < 1.0 and median_height and p10_height:
            projected_median = float(median_height) * publication_scale
            projected_p10 = float(p10_height) * publication_scale
            # Poppler word boxes are usually somewhat shorter than the declared
            # font size. Keep this warning intentionally conservative.
            if projected_median < minimum_text_pt * 0.72:
                warnings.append(
                    "projected text appears too small after publication scaling: "
                    f"median word box {projected_median:.1f} pt at target width "
                    f"(minimum text baseline {minimum_text_pt:.1f} pt)"
                )
            elif projected_p10 < minimum_text_pt * 0.50:
                warnings.append(
                    "some text may become too small after publication scaling: "
                    f"10th-percentile word box {projected_p10:.1f} pt at target width"
                )

    size_check = {
        "natural_width_mm": info.get("width_mm"),
        "natural_height_mm": info.get("height_mm"),
        "target_width_mm": round(target_width_mm, 2) if target_width_mm else None,
        "target_source": target_source,
        "minimum_text_pt": minimum_text_pt or None,
        "scale_to_target": round(publication_scale, 4) if target_width_mm else None,
        "projected_width_mm": (projected_size or {}).get("width_mm"),
        "projected_height_mm": (projected_size or {}).get("height_mm"),
    }

    preview = figure_dir / ".funfig" / "preview.png"
    _render_preview(pdf, preview, dpi=dpi)

    manifest_file = figure_dir / ".funfig" / "manifest.json"
    if not manifest_file.is_file():
        raise QAError(f"manifest does not exist: {manifest_file}")
    manifest = load_json(manifest_file)
    previous_qa = manifest.get("qa") or {}
    review_history = list(previous_qa.get("review_history") or [])
    manifest["qa"] = {
        "status": "preview_ready",
        "machine_checks_passed": not warnings,
        "visual_review": "pending",
        "warnings": warnings,
        "pdf": info,
        "text_metrics": text_metrics,
        "size_check": size_check,
        "publication_projection": projected_size,
        "preview": ".funfig/preview.png",
        "preview_dpi": int(dpi),
        "checked_at": utc_now(),
        "review_history": review_history,
        "review_count": len(review_history),
        "repair_cycles": sum(1 for item in review_history if item.get("result") == "failed"),
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
    reviewed_at = utc_now()
    result = "passed" if passed else "failed"
    qa["visual_review"] = result
    qa["status"] = "passed" if passed and qa.get("machine_checks_passed", True) else "failed"
    qa["review_note"] = note
    qa["reviewed_at"] = reviewed_at
    history = qa.setdefault("review_history", [])
    history.append({
        "result": result,
        "note": note,
        "reviewed_at": reviewed_at,
    })
    qa["review_count"] = len(history)
    qa["repair_cycles"] = sum(1 for item in history if item.get("result") == "failed")
    write_manifest(figure_dir, manifest)
    return qa
