#!/usr/bin/env python3
"""Build verified PGF/TikZ manual excerpts and a lightweight search corpus.

The script uses only the Python standard library plus qpdf/Poppler command-line
tools. qpdf performs page-object selection without re-rendering/re-encoding the
manual; Poppler is used for source verification, text extraction, and QA. The
original PDF is never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "references/manuals/pgfmanual-3.1.11a"
SOURCE_FILE = MANIFEST_DIR / "source.json"
PLAN_FILE = MANIFEST_DIR / "split-plan.json"
TOPICS_FILE = MANIFEST_DIR / "topics.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        list(args), check=False, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"command failed: {' '.join(args)}")
    return result.stdout if capture else ""


def require_tools(*names: str) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise RuntimeError("missing required tools: " + ", ".join(missing))


def verify_source() -> tuple[dict, Path]:
    require_tools("pdfinfo", "pdftotext")
    source = load_json(SOURCE_FILE)
    pdf = ROOT / source["source_path"]
    if not pdf.is_file():
        raise RuntimeError(f"manual source is missing: {pdf}")
    actual_sha = sha256(pdf)
    if actual_sha != source["sha256"]:
        raise RuntimeError(f"SHA-256 mismatch: expected {source['sha256']}, got {actual_sha}")
    info = run("pdfinfo", str(pdf), capture=True)
    match = re.search(r"^Pages:\s+(\d+)$", info, flags=re.MULTILINE)
    pages = int(match.group(1)) if match else None
    if pages != source["page_count"]:
        raise RuntimeError(f"page count mismatch: expected {source['page_count']}, got {pages}")
    return source, pdf


def validate_plan(source: dict, plan: dict) -> None:
    coverage: list[int] = []
    for part in plan["parts"]:
        for start, end in part["source_ranges"]:
            if start < 1 or end < start or end > source["page_count"]:
                raise RuntimeError(f"invalid range {start}-{end} in {part['id']}")
            coverage.extend(range(start, end + 1))
    expected = list(range(1, source["page_count"] + 1))
    if coverage != expected:
        raise RuntimeError("first-level split plan must cover every source page exactly once in order")


def _page_spec(ranges: list[list[int]]) -> str:
    return ",".join(str(start) if start == end else f"{start}-{end}" for start, end in ranges)


def extract_pdf(pdf: Path, ranges: list[list[int]], output: Path) -> str:
    require_tools("qpdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    selection = _page_spec(ranges)
    # Keep `.pdf` as the final suffix: some PDF backends reject `.pdf.tmp`.
    temporary = output.with_name(f".{output.stem}.tmp.pdf")
    temporary.unlink(missing_ok=True)
    run("qpdf", "--empty", "--pages", str(pdf), selection, "--", str(temporary))
    backend = "qpdf-page-copy"
    temporary.replace(output)
    return backend


def _pdf_pages_and_size(pdf: Path) -> tuple[int, tuple[float, float]]:
    info = run("pdfinfo", str(pdf), capture=True)
    pages_match = re.search(r"^Pages:\s+(\d+)$", info, flags=re.MULTILINE)
    size_match = re.search(
        r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        info,
        flags=re.MULTILINE,
    )
    if not pages_match or not size_match:
        raise RuntimeError(f"could not read page count/size from {pdf}")
    return int(pages_match.group(1)), (float(size_match.group(1)), float(size_match.group(2)))


def _annotation_warning_count(pdf: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"pdfinfo failed for {pdf}")
    return sum(
        1 for line in result.stderr.splitlines()
        if "Illegal annotation destination" in line
    )


def _pdfinfo_warnings(pdf: Path) -> list[str]:
    result = subprocess.run(
        ["pdfinfo", str(pdf)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"pdfinfo failed for {pdf}")
    return [line.strip() for line in result.stderr.splitlines() if line.strip()]


def _normalized_page_text(pdf: Path, page: int) -> str:
    text = run("pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-", capture=True)
    return re.sub(r"\s+", "", text)


def _render_ppm(pdf: Path, page: int, directory: Path, stem: str) -> bytes:
    prefix = directory / stem
    run(
        "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-r", "96",
        str(pdf), str(prefix),
    )
    ppm = prefix.with_suffix(".ppm")
    if not ppm.is_file():
        raise RuntimeError(f"pdftoppm did not create {ppm}")
    return ppm.read_bytes()


def _byte_diff_ratio(left: bytes, right: bytes) -> float:
    if len(left) != len(right):
        return 1.0
    if not left:
        return 0.0
    return sum(a != b for a, b in zip(left, right)) / len(left)


def verify_split_artifact(source_pdf: Path, output_pdf: Path, ranges: list[list[int]]) -> dict:
    require_tools("pdfinfo", "pdftotext", "pdftoppm")
    expected_pages = sum(end - start + 1 for start, end in ranges)
    actual_pages, output_size = _pdf_pages_and_size(output_pdf)
    _, source_size = _pdf_pages_and_size(source_pdf)
    if actual_pages != expected_pages:
        raise RuntimeError(
            f"split page count mismatch for {output_pdf.name}: expected {expected_pages}, got {actual_pages}"
        )
    if any(abs(a - b) > 0.02 for a, b in zip(output_size, source_size)):
        raise RuntimeError(
            f"split page box mismatch for {output_pdf.name}: source={source_size}, output={output_size}"
        )

    source_pages = [ranges[0][0], ranges[-1][1]]
    output_pages = [1, expected_pages]
    checks = []
    with tempfile.TemporaryDirectory(prefix="tff-manual-qa-") as temp:
        tempdir = Path(temp)
        for index, (source_page, output_page) in enumerate(zip(source_pages, output_pages)):
            if _normalized_page_text(source_pdf, source_page) != _normalized_page_text(output_pdf, output_page):
                raise RuntimeError(
                    f"split text mismatch for {output_pdf.name}: source page {source_page} -> output page {output_page}"
                )
            source_render = _render_ppm(source_pdf, source_page, tempdir, f"source-{index}")
            output_render = _render_ppm(output_pdf, output_page, tempdir, f"output-{index}")
            ratio = _byte_diff_ratio(source_render, output_render)
            if ratio > 0.03:
                raise RuntimeError(
                    f"split render drift {ratio:.4%} exceeds 3% for {output_pdf.name}: "
                    f"source page {source_page} -> output page {output_page}"
                )
            checks.append({
                "source_page": source_page,
                "output_page": output_page,
                "normalized_text_equal": True,
                "render_byte_diff_ratio_96dpi": round(ratio, 8),
            })
    return {
        "page_count": actual_pages,
        "page_size_points": [output_size[0], output_size[1]],
        "representative_checks": checks,
        "invalid_annotation_destinations_reported": _annotation_warning_count(output_pdf),
    }


HEADING = re.compile(r"^\s*(\d+(?:\.\d+){0,3})\s+([^\n]{3,110})\s*$")
COMMAND = re.compile(r"\\[A-Za-z@]+")
KEY = re.compile(r"/(?:tikz|pgf|pgfplots)/[A-Za-z0-9 ._:/-]+")
LIBRARY_DECL = re.compile(r"\\use(?:tikz|pgf)library\s*\{([^}]+)\}")
CODE_HINT = re.compile(r"\\(?:begin\{tikzpicture\}|tikz\b|draw\b|path\b|node\b|coordinate\b)")


def _page_heading(text: str) -> tuple[str | None, str | None]:
    for raw in text.splitlines()[:55]:
        match = HEADING.match(raw)
        if match and not re.search(r"\.{3,}|\s\d{2,4}\s*$", raw):
            return match.group(1), match.group(2).strip()
    return None, None


def _section_level(number: str | None) -> int:
    return number.count(".") + 1 if number else 0


def _parent_section(number: str | None) -> str | None:
    if not number or "." not in number:
        return None
    return number.rsplit(".", 1)[0]


def _declared_libraries(text: str) -> list[str]:
    names: list[str] = []
    for raw in LIBRARY_DECL.findall(text):
        for name in raw.split(","):
            cleaned = name.strip()
            if cleaned:
                names.append(cleaned)
    return sorted(set(names))


def build_corpus(source: dict, pdf: Path) -> Path:
    topics = load_json(TOPICS_FILE)["topics"]
    text = run("pdftotext", "-layout", str(pdf), "-", capture=True)
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != source["page_count"]:
        raise RuntimeError(f"pdftotext page count mismatch: expected {source['page_count']}, got {len(pages)}")

    chunks: list[dict] = []
    active_number: str | None = None
    active_title = "Unnumbered section"
    bucket: list[tuple[int, str]] = []

    def flush() -> None:
        nonlocal bucket
        if not bucket:
            return
        first, last = bucket[0][0], bucket[-1][0]
        body = "\n".join(item[1].strip() for item in bucket if item[1].strip())
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        commands = sorted(set(COMMAND.findall(body)))[:80]
        keys = sorted(set(value.strip() for value in KEY.findall(body)))[:80]
        topic_ids: list[str] = []
        aliases: list[str] = []
        libraries: list[str] = []
        for topic in topics:
            if any(start <= last and end >= first for start, end in topic["source_ranges"]):
                topic_ids.append(topic["id"])
                aliases.extend(topic.get("aliases", []))
                libraries.extend(topic.get("libraries", []))
        libraries.extend(_declared_libraries(body))
        chunks.append({
            "id": f"{source['source_id']}-p{first:04d}-{last:04d}",
            "source_id": source["source_id"],
            "version": source["version"],
            "section": active_number,
            "section_level": _section_level(active_number),
            "parent_section": _parent_section(active_number),
            "title": active_title,
            "page_start": first,
            "page_end": last,
            "page_labels": [str(first), str(last)],
            "topic_ids": sorted(set(topic_ids)),
            "aliases": sorted(set(aliases)),
            "libraries": sorted(set(libraries)),
            "commands": commands,
            "keys": keys,
            "contains_code_example": bool(CODE_HINT.search(body)),
            "contains_figure_hint": "figure" in body.casefold() or "illustration" in body.casefold(),
            # Keep the distributable corpus bounded while retaining commands and nearby prose.
            "text": body[:12000],
        })
        bucket = []

    for page_no, page_text in enumerate(pages, start=1):
        number, title = _page_heading(page_text)
        heading_changed = number is not None and (number != active_number or title != active_title)
        if bucket and (heading_changed or len(bucket) >= 4):
            flush()
        if number is not None:
            active_number, active_title = number, title or active_title
        bucket.append((page_no, page_text))
    flush()

    for index, chunk in enumerate(chunks):
        chunk["previous_id"] = chunks[index - 1]["id"] if index else None
        chunk["next_id"] = chunks[index + 1]["id"] if index + 1 < len(chunks) else None

    destination = ROOT / "knowledge/manual-index" / f"{source['source_id']}.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for chunk in chunks:
            stream.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(destination)

    library_index: dict[str, dict] = {}
    for chunk in chunks:
        if chunk["page_end"] < 564 or chunk["page_start"] > 852:
            continue
        for library in chunk.get("libraries", []):
            record = library_index.setdefault(
                library,
                {"library": library, "source_id": source["source_id"], "chunk_ids": [], "pages": []},
            )
            record["chunk_ids"].append(chunk["id"])
            record["pages"].append([chunk["page_start"], chunk["page_end"]])
    library_path = destination.with_name(f"{source['source_id']}.libraries.json")
    library_path.write_text(
        json.dumps(
            {"source_id": source["source_id"], "libraries": list(library_index.values())},
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    return destination


def build_pdfs(source: dict, pdf: Path) -> Path:
    plan = load_json(PLAN_FILE)
    validate_plan(source, plan)
    output = ROOT / "output/pdf" / source["source_id"]
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for collection in ("parts", "focus_excerpts"):
        for item in plan[collection]:
            target = output / item["filename"]
            print(f"building {collection}: {item['id']} -> {target.name}", flush=True)
            backend = extract_pdf(pdf, item["source_ranges"], target)
            qa = verify_split_artifact(pdf, target, item["source_ranges"])
            records.append({
                "id": item["id"], "filename": item["filename"],
                "source_ranges": item["source_ranges"], "sha256": sha256(target),
                "backend": backend,
                "qa": qa,
                "link_policy": "Generated booklets preserve original page content and annotations. Cross-document destinations can become invalid after page selection; the QA report records their count. Use the original manual for authoritative hyperlinks/navigation.",
            })
    report = {"source_id": source["source_id"], "source_sha256": source["sha256"], "artifacts": records}
    (output / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "corpus", "pdfs", "all"))
    args = parser.parse_args(argv)
    try:
        source, pdf = verify_source()
        validate_plan(source, load_json(PLAN_FILE))
        if args.command in {"corpus", "all"}:
            print(f"corpus: {build_corpus(source, pdf)}")
        if args.command in {"pdfs", "all"}:
            print(f"pdfs: {build_pdfs(source, pdf)}")
        print(f"ok: {source['source_id']} sha={source['sha256']} pages={source['page_count']}")
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
