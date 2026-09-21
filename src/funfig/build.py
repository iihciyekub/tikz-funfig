from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .io import load_json
from .manifest import manifest_path, sha256_file, utc_now, write_manifest
from .render import dependencies_for_spec, output_formats_for_spec, render_spec


class BuildError(RuntimeError):
    pass


def _engine(spec: dict[str, Any], tex_path: Path) -> str:
    configured = (spec.get("engine") or {}).get("latex", "auto")
    if configured != "auto":
        return configured
    text = tex_path.read_text(encoding="utf-8")
    if any(ord(char) > 127 for char in text) or "xeCJK" in text or "fontspec" in text:
        return "xelatex"
    return "pdflatex"


def doctor(spec: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    required = ["latexmk", "pdflatex", "xelatex"]
    if spec is not None and dependencies_for_spec(spec)["gnuplot"]:
        required.append("gnuplot")
    if spec is not None and dependencies_for_spec(spec)["pdftocairo"]:
        required.append("pdftocairo")
    messages: list[str] = []
    ok = True
    for command in required:
        path = shutil.which(command)
        if path:
            messages.append(f"ok      {command}: {path}")
        else:
            ok = False
            messages.append(f"missing {command}")
    return ok, messages


def _relocate_transients(figure_dir: Path, basename: str, build_dir: Path) -> None:
    suffixes = [
        "aux",
        "bbl",
        "bcf",
        "blg",
        "fdb_latexmk",
        "fls",
        "log",
        "out",
        "run.xml",
        "synctex.gz",
        "toc",
        "pgf-plot.gnuplot",
        "pgf-plot.table",
        "gnuplot",
        "table",
    ]
    for suffix in suffixes:
        source = figure_dir / f"{basename}.{suffix}"
        if source.exists():
            destination = build_dir / source.name
            if destination.exists():
                destination.unlink()
            shutil.move(str(source), str(destination))

    # PGFPlots' `contour gnuplot` handler uses underscore-based temporary
    # names such as `<basename>_contourtmp0.script` and `.dat`, rather than
    # the dot-suffix convention used by most TeX/PGFPlots intermediates.
    # Keep them under the same disposable build contract.
    for source in figure_dir.glob(f"{basename}_contourtmp*"):
        if not source.is_file():
            continue
        destination = build_dir / source.name
        if destination.exists():
            destination.unlink()
        shutil.move(str(source), str(destination))


def build_spec(spec: dict[str, Any], spec_path: Path) -> Path:
    tex_path, manifest = render_spec(spec, spec_path)
    figure_dir = spec_path.parent
    basename = (spec.get("outputs") or {}).get("basename", "figure")
    output_formats = output_formats_for_spec(spec)
    final_pdf = figure_dir / f"{basename}.pdf"
    final_svg = figure_dir / f"{basename}.svg"
    build_dir = figure_dir / ".funfig" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    tools_ok, messages = doctor(spec)
    if not tools_ok:
        raise BuildError("dependency check failed:\n" + "\n".join(messages))

    engine = _engine(spec, tex_path)
    # Compile from the figure directory instead of using latexmk -outdir.
    # PGFPlots' gnuplot handler launches gnuplot with filenames relative to
    # the TeX working directory; -outdir would place the generated script in
    # another directory and break raw gnuplot. Intermediates are relocated
    # into .funfig/build immediately after latexmk exits.
    command = [
        "latexmk",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
    ]
    if engine == "xelatex":
        command.append("-xelatex")
    elif engine == "lualatex":
        command.append("-lualatex")
    else:
        command.append("-pdf")
    if dependencies_for_spec(spec)["shell_escape"]:
        command.append("-latexoption=-shell-escape")
    command.append(tex_path.name)

    process = subprocess.run(
        command,
        cwd=figure_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    _relocate_transients(figure_dir, basename, build_dir)
    log_path = build_dir / "funfig-build.log"
    log_path.write_text(process.stdout, encoding="utf-8")

    if process.returncode != 0:
        manifest.update(
            {
                "status": "build_failed",
                "updated_at": utc_now(),
                "build": {
                    "engine": engine,
                    "command": command,
                    "returncode": process.returncode,
                    "log": ".funfig/build/funfig-build.log",
                },
            }
        )
        write_manifest(figure_dir, manifest)
        tail = "\n".join(process.stdout.splitlines()[-40:])
        raise BuildError(f"LaTeX build failed; see {log_path}\n{tail}")

    if not final_pdf.exists():
        raise BuildError(f"build succeeded but PDF was not found: {final_pdf}")

    manifest.update(
        {
            "status": "built",
            "updated_at": utc_now(),
            "build": {
                "engine": engine,
                "command": command,
                "returncode": process.returncode,
            },
        }
    )
    manifest["hashes"]["pdf_sha256"] = sha256_file(final_pdf)

    if "svg" in output_formats:
        staged_svg = build_dir / f"{basename}.svg"
        svg_command = [
            "pdftocairo",
            "-svg",
            str(final_pdf),
            str(staged_svg),
        ]
        svg_process = subprocess.run(
            svg_command,
            cwd=figure_dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        (build_dir / "funfig-svg.log").write_text(svg_process.stdout, encoding="utf-8")
        if svg_process.returncode != 0 or not staged_svg.is_file():
            manifest.update(
                {
                    "status": "artifact_failed",
                    "updated_at": utc_now(),
                    "svg": {
                        "command": svg_command,
                        "returncode": svg_process.returncode,
                        "log": ".funfig/build/funfig-svg.log",
                    },
                }
            )
            write_manifest(figure_dir, manifest)
            tail = "\n".join(svg_process.stdout.splitlines()[-40:])
            raise BuildError(f"PDF built but SVG export failed; see {build_dir / 'funfig-svg.log'}\n{tail}")
        staged_svg.replace(final_svg)
        manifest["hashes"]["svg_sha256"] = sha256_file(final_svg)
        manifest["svg"] = {"command": svg_command, "returncode": 0}

    keep_build = bool((spec.get("outputs") or {}).get("keep_build", False))
    if not keep_build:
        shutil.rmtree(build_dir)
        manifest["build"]["intermediates_cleaned"] = True
    else:
        manifest["build"]["intermediates_cleaned"] = False
        manifest["build"]["log"] = ".funfig/build/funfig-build.log"
    write_manifest(figure_dir, manifest)
    return final_pdf


def clean_spec(spec: dict[str, Any], spec_path: Path) -> list[Path]:
    figure_dir = spec_path.parent
    basename = (spec.get("outputs") or {}).get("basename", "figure")
    removed: list[Path] = []
    build_dir = figure_dir / ".funfig" / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
        removed.append(build_dir)
    for suffix in ("pgf-plot.gnuplot", "pgf-plot.table", "gnuplot", "table"):
        path = figure_dir / f"{basename}.{suffix}"
        if path.exists():
            path.unlink()
            removed.append(path)
    for path in figure_dir.glob(f"{basename}_contourtmp*"):
        if path.is_file():
            path.unlink()
            removed.append(path)

    current_manifest = manifest_path(figure_dir)
    if current_manifest.exists():
        manifest = load_json(current_manifest)
        manifest["updated_at"] = utc_now()
        manifest.setdefault("cleanup_events", []).append(
            {"at": utc_now(), "removed": [str(path.relative_to(figure_dir)) for path in removed]}
        )
        write_manifest(figure_dir, manifest)
    return removed

