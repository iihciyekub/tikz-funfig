from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .io import write_text_atomic
from .manifest import sha256_file, utc_now, write_manifest
from .recipes import load_recipe
from .schema import validate_spec


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _style_options(style: dict[str, Any] | None) -> list[str]:
    if not style:
        return []
    result: list[str] = []
    mapping = {
        "color": lambda value: str(value),
        "line": lambda value: str(value),
        "line_width": lambda value: f"line width={value}",
        "opacity": lambda value: f"opacity={_fmt(value)}",
        "mark": lambda value: f"mark={value}",
        "mark_size": lambda value: f"mark size={value}",
        "draw": lambda value: f"draw={value}",
        "fill": lambda value: f"fill={value}",
        "fill_opacity": lambda value: f"fill opacity={_fmt(value)}",
    }
    for key, formatter in mapping.items():
        if key in style:
            result.append(formatter(style[key]))
    return result


def _axis_options(spec: dict[str, Any], axes: dict[str, Any] | None = None) -> list[str]:
    axes = axes or spec.get("axes", {}) or {}
    canvas = spec.get("canvas", {}) or {}
    options = [
        f"width={canvas.get('width', '10cm')}",
        f"height={canvas.get('height', '7cm')}",
    ]
    grid = axes.get("grid", "major")
    if grid != "none":
        options.append(f"grid={grid}")
        options.append("grid style={gray!25,line width=0.2pt}")

    if axes.get("title"):
        options.append(f"title={{{axes['title']}}}")
        options.append("title style={align=left}")
    if axes.get("axis_line_shift"):
        options.append(f"axis line shift={axes['axis_line_shift']}")
    if axes.get("tick_precision") is not None:
        options.append(
            "ticklabel style={/pgf/number format/precision="
            f"{int(axes['tick_precision'])}" + "}"
        )

    for key in ("x", "y", "z"):
        axis = axes.get(key) or {}
        if axis.get("label") is not None:
            options.append(f"{key}label={{{axis['label']}}}")
        if axis.get("min") is not None:
            options.append(f"{key}min={_fmt(axis['min'])}")
        if axis.get("max") is not None:
            options.append(f"{key}max={_fmt(axis['max'])}")
        ticks = axis.get("ticks")
        if isinstance(ticks, list) and ticks:
            options.append(f"{key}tick={{{','.join(_fmt(v) for v in ticks)}}}")
        tick_labels = axis.get("tick_labels")
        if isinstance(tick_labels, list) and tick_labels:
            options.append(f"{key}ticklabels={{{','.join(tick_labels)}}}")
        if axis.get("dir") == "reverse":
            options.append(f"{key} dir=reverse")

    legend = axes.get("legend") or {}
    legend_position = legend.get("position") or axes.get("legend_position")
    if legend_position:
        options.append(f"legend pos={legend_position}")
    legend_style = ["draw=none", "fill=none"]
    cell_anchor = legend.get("cell_anchor", "west")
    legend_style.append(f"cells={{anchor={cell_anchor}}}")
    if legend.get("at"):
        legend_style.append(f"at={{{legend['at']}}}")
    if legend.get("anchor"):
        legend_style.append(f"anchor={legend['anchor']}")
    if legend.get("columns"):
        legend_style.append(f"legend columns={int(legend['columns'])}")
    if legend.get("font"):
        legend_style.append(f"font={legend['font']}")
    options.append(f"legend style={{{','.join(legend_style)}}}")
    return options


def _source_map(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {source["id"]: source for source in spec.get("data_sources", [])}


def _series_map(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {series["id"]: series for series in spec.get("series", [])}


def _render_series(series: dict[str, Any], source: dict[str, Any]) -> list[str]:
    options = _style_options(series.get("style"))
    # Do not inherit PGFPlots' cycle-list marker by accident. A FunFig series
    # is a line by default; markers are opt-in through style.mark. This keeps
    # rendering deterministic across cycle-list/theme changes and matches the
    # publication figures in the local knowledge base.
    if not any(option.startswith("mark=") for option in options):
        options.append("mark=none")
    options.extend(series.get("options", []) or [])
    if series.get("name_path"):
        options.append(f"name path={series['name_path']}")

    source_type = source["type"]
    if source.get("domain"):
        options.append(f"domain={source['domain']}")
    if source.get("samples"):
        options.append(f"samples={source['samples']}")

    bracket = f"[{','.join(options)}]" if options else ""
    if source_type == "function":
        plot = f"\\addplot+ {bracket} {{{source['expression']}}};"
    elif source_type == "file":
        columns = []
        for key in ("x", "y", "z"):
            if source.get(key):
                columns.append(f"{key}={source[key]}")
        table_options = f"[{','.join(columns)}]" if columns else ""
        command = "\\addplot3" if source.get("z") else "\\addplot+"
        plot = f"{command} {bracket} table{table_options} {{{source['path']}}};"
    elif source_type == "coordinates":
        points = " ".join(
            "(" + ",".join(_fmt(value) for value in point) + ")"
            for point in source.get("points", [])
        )
        plot = f"\\addplot+ {bracket} coordinates {{{points}}};"
    elif source_type == "gnuplot":
        gp_options = ",".join(options)
        gp_bracket = f"[{gp_options}]" if gp_options else ""
        plot = f"\\addplot+ gnuplot{gp_bracket} {{{source['expression']}}};"
    elif source_type == "raw_gnuplot":
        gp_options = ["raw gnuplot"] + options
        plot = f"\\addplot+ gnuplot[{','.join(gp_options)}] {{\n{source['script']}\n}};"
    else:
        raise ValueError(f"unsupported data source type: {source_type}")

    lines = [plot]
    if series.get("label"):
        lines.append(f"\\addlegendentry{{{series['label']}}}")
    return lines


def _render_regions(spec: dict[str, Any], between: bool) -> list[str]:
    lines: list[str] = []
    for region in spec.get("regions", []):
        region_type = region.get("type")
        if between != (region_type == "between"):
            continue
        style = _style_options(region.get("style"))
        bracket = f"[{','.join(style)}]" if style else ""
        if region_type == "rectangle":
            lines.append(
                f"\\fill {bracket} (axis cs:{_fmt(region['x1'])},{_fmt(region['y1'])}) "
                f"rectangle (axis cs:{_fmt(region['x2'])},{_fmt(region['y2'])});"
            )
        elif region_type == "between":
            fill_opts = [f"of={region['path_a']} and {region['path_b']}"]
            if region.get("domain"):
                fill_opts.append(f"soft clip={{domain={region['domain']}}}")
            lines.append(
                f"\\addplot {bracket} fill between [{','.join(fill_opts)}];"
            )
    return lines


def _render_annotations(spec: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for index, annotation in enumerate(spec.get("annotations", []), start=1):
        kind = annotation.get("type")
        style = _style_options(annotation.get("style"))
        style_text = ",".join(style)
        extra = f",{style_text}" if style_text else ""
        if kind == "point":
            x, y = annotation["at"]
            marker_style = list(style)
            marker_style.extend(["only marks"])
            if not any(option.startswith("mark=") for option in marker_style):
                marker_style.append("mark=*")
            if not any(option.startswith("mark size=") for option in marker_style):
                marker_style.append("mark size=1.6pt")
            lines.append(
                f"\\addplot+[{','.join(marker_style)}] coordinates "
                f"{{({_fmt(x)},{_fmt(y)})}};"
            )
            if annotation.get("label"):
                anchor = annotation.get("anchor", "south west")
                shift = annotation.get("shift", "(2pt,2pt)")
                node_name = f"funfigCallout{index}"
                node_options = [f"anchor={anchor}"]
                if annotation.get("font"):
                    node_options.append(f"font={annotation['font']}")
                if annotation.get("rotate") is not None:
                    node_options.append(f"rotate={_fmt(annotation['rotate'])}")
                lines.append(
                    f"\\node[{','.join(node_options)}] ({node_name}) at "
                    f"([shift={{{shift}}}]axis cs:{_fmt(x)},{_fmt(y)}) {{{annotation['label']}}};"
                )
                if annotation.get("arrow"):
                    arrow_options = annotation.get("arrow_style") or ["-{Stealth[length=4pt,width=3pt]}", "shorten >=1pt"]
                    arrow_anchor = annotation.get("arrow_anchor", "center")
                    lines.append(
                        f"\\draw[{','.join(arrow_options)}] ({node_name}.{arrow_anchor}) -- "
                        f"(axis cs:{_fmt(x)},{_fmt(y)});"
                    )
        elif kind == "label":
            x, y = annotation["at"]
            anchor = annotation.get("anchor", "center")
            node_options = [f"anchor={anchor}"]
            node_options.extend(style)
            if annotation.get("font"):
                node_options.append(f"font={annotation['font']}")
            if annotation.get("rotate") is not None:
                node_options.append(f"rotate={_fmt(annotation['rotate'])}")
            lines.append(
                f"\\node[{','.join(node_options)}] at (axis cs:{_fmt(x)},{_fmt(y)}) "
                f"{{{annotation.get('label', '')}}};"
            )
        elif kind == "vline":
            x = annotation["x"]
            lines.append(
                f"\\draw[{style_text}] (axis cs:{_fmt(x)},\\pgfkeysvalueof{{/pgfplots/ymin}}) -- "
                f"(axis cs:{_fmt(x)},\\pgfkeysvalueof{{/pgfplots/ymax}});"
            )
        elif kind == "hline":
            y = annotation["y"]
            lines.append(
                f"\\draw[{style_text}] (axis cs:\\pgfkeysvalueof{{/pgfplots/xmin}},{_fmt(y)}) -- "
                f"(axis cs:\\pgfkeysvalueof{{/pgfplots/xmax}},{_fmt(y)});"
            )
        elif kind == "intersection":
            name = annotation.get("name", f"intersection{index}")
            lines.append(
                f"\\path[name intersections={{of={annotation['path_a']} and {annotation['path_b']},by={name}}}];"
            )
            raw_style = annotation.get("style") or {}
            marker_draw = []
            if raw_style.get("fill"):
                marker_draw.append(f"fill={raw_style['fill']}")
            if raw_style.get("draw"):
                marker_draw.append(f"draw={raw_style['draw']}")
            elif raw_style.get("color"):
                marker_draw.append(f"draw={raw_style['color']}")
            if raw_style.get("opacity") is not None:
                marker_draw.append(f"opacity={_fmt(raw_style['opacity'])}")
            marker_draw.append("line width=0.45pt")
            lines.append(f"\\draw[{','.join(marker_draw)}] ({name}) circle (0.7mm);")
            if annotation.get("label"):
                anchor = annotation.get("anchor", "south west")
                shift = annotation.get("shift", "(2pt,2pt)")
                node_name = f"funfigIntersectionCallout{index}"
                node_options = [f"anchor={anchor}"]
                if annotation.get("font"):
                    node_options.append(f"font={annotation['font']}")
                lines.append(
                    f"\\node[{','.join(node_options)}] ({node_name}) at "
                    f"([shift={{{shift}}}]{name}) {{{annotation['label']}}};"
                )
                if annotation.get("arrow"):
                    arrow_options = annotation.get("arrow_style") or ["-{Stealth[length=4pt,width=3pt]}", "shorten >=1pt"]
                    arrow_anchor = annotation.get("arrow_anchor", "center")
                    lines.append(
                        f"\\draw[{','.join(arrow_options)}] ({node_name}.{arrow_anchor}) -- ({name});"
                    )
    return lines


def _document_preamble(spec: dict[str, Any], groupplots: bool = False) -> list[str]:
    border = (spec.get("canvas") or {}).get("border", "2pt")
    lines = [
        f"\\documentclass[border={border}]{{standalone}}",
        "\\usepackage[dvipsnames,svgnames,x11names]{xcolor}",
        "\\usepackage{tikz}",
        "\\usepackage{pgfplots}",
        "\\pgfplotsset{compat=1.18}",
        "\\usetikzlibrary{calc,arrows.meta,positioning,intersections,fit,shapes.geometric}",
        "\\usepgfplotslibrary{fillbetween}",
    ]
    if groupplots:
        lines.append("\\usepgfplotslibrary{groupplots}")
    return lines


def render_pgfplots(spec: dict[str, Any]) -> str:
    sources = _source_map(spec)
    lines = _document_preamble(spec)
    lines += ["", "\\begin{document}", "\\begin{tikzpicture}"]
    axis_options = _axis_options(spec)
    lines.append("\\begin{axis}[")
    lines.extend(f"  {option}," for option in axis_options)
    lines.append("]")

    lines.extend(_render_regions(spec, between=False))
    for series in spec.get("series", []):
        lines.extend(_render_series(series, sources[series["source"]]))
    lines.extend(_render_regions(spec, between=True))
    lines.extend(_render_annotations(spec))
    lines += ["\\end{axis}", "\\end{tikzpicture}", "\\end{document}", ""]
    return "\n".join(lines)


def render_groupplot(spec: dict[str, Any]) -> str:
    sources = _source_map(spec)
    series_by_id = _series_map(spec)
    panels = spec.get("panels", [])
    columns = int((spec.get("metadata") or {}).get("group_columns", min(2, max(1, len(panels)))))
    rows = max(1, math.ceil(len(panels) / columns))
    lines = _document_preamble(spec, groupplots=True)
    lines += ["", "\\begin{document}", "\\begin{tikzpicture}"]
    lines.append("\\begin{groupplot}[")
    lines.append(
        f"  group style={{group size={columns} by {rows},horizontal sep=1.5cm,vertical sep=1.2cm}},"
    )
    for option in _axis_options(spec):
        lines.append(f"  {option},")
    lines.append("]")

    for panel in panels:
        panel_options = []
        if panel.get("title"):
            panel_options.append(f"title={{{panel['title']}}}")
        panel_options.extend(_axis_options(spec, panel.get("axes")))
        lines.append(f"\\nextgroupplot[{','.join(panel_options)}]")
        for series_id in panel.get("series", []):
            series = series_by_id[series_id]
            lines.extend(_render_series(series, sources[series["source"]]))

    lines += ["\\end{groupplot}", "\\end{tikzpicture}", "\\end{document}", ""]
    return "\n".join(lines)


def render_diagram(spec: dict[str, Any]) -> str:
    border = (spec.get("canvas") or {}).get("border", "2pt")
    diagram = spec.get("diagram", {}) or {}
    lines = [
        f"\\documentclass[border={border}]{{standalone}}",
        "\\usepackage[dvipsnames,svgnames,x11names]{xcolor}",
        "\\usepackage{tikz}",
        "\\usetikzlibrary{calc,arrows.meta,positioning,fit,shapes.geometric}",
        "\\tikzset{",
        "  funfig node/.style={draw,rounded corners=2pt,minimum height=8mm,inner xsep=7pt,inner ysep=4pt,align=center},",
        "  funfig edge/.style={-{Stealth[length=5pt,width=4pt]},line width=0.65pt},",
        "}",
        "\\begin{document}",
        "\\begin{tikzpicture}[node distance=12mm and 18mm]",
    ]
    for node in diagram.get("nodes", []):
        options = ["funfig node"] + list(node.get("style", []) or [])
        if node.get("at"):
            position = f" at ({node['at']})"
        elif node.get("right_of"):
            options.append(f"right=of {node['right_of']}")
            position = ""
        elif node.get("below_of"):
            options.append(f"below=of {node['below_of']}")
            position = ""
        else:
            position = ""
        lines.append(
            f"\\node[{','.join(options)}] ({node['id']}){position} {{{node['label']}}};"
        )
    for edge in diagram.get("edges", []):
        options = ["funfig edge"] + list(edge.get("style", []) or [])
        label = f" node[midway,above] {{{edge['label']}}}" if edge.get("label") else ""
        lines.append(
            f"\\draw[{','.join(options)}] ({edge['from']}) --{label} ({edge['to']});"
        )
    lines += ["\\end{tikzpicture}", "\\end{document}", ""]
    return "\n".join(lines)


def dependencies_for_spec(spec: dict[str, Any]) -> dict[str, Any]:
    source_types = {source.get("type") for source in spec.get("data_sources", [])}
    needs_gnuplot = bool(source_types & {"gnuplot", "raw_gnuplot"}) or (
        (spec.get("engine") or {}).get("compute") == "gnuplot"
    )
    return {
        "latexmk": True,
        "gnuplot": needs_gnuplot,
        "shell_escape": needs_gnuplot,
    }


def render_spec(spec: dict[str, Any], spec_path: Path) -> tuple[Path, dict[str, Any]]:
    validation = validate_spec(spec, spec_path)
    if not validation.ok:
        raise ValueError("invalid FigureSpec:\n- " + "\n- ".join(validation.errors))

    recipe = load_recipe(spec["recipe"])
    renderer = recipe["renderer"]
    if renderer == "pgfplots":
        text = render_pgfplots(spec)
    elif renderer == "groupplot":
        text = render_groupplot(spec)
    elif renderer == "diagram":
        text = render_diagram(spec)
    else:
        raise ValueError(f"unsupported renderer: {renderer}")

    figure_dir = spec_path.parent
    basename = (spec.get("outputs") or {}).get("basename", "figure")
    tex_path = figure_dir / f"{basename}.tex"
    write_text_atomic(tex_path, text)

    manifest = {
        "manifest_version": "1.0",
        "figure_id": spec["id"],
        "schema_version": spec["schema_version"],
        "recipe": {"id": recipe["id"], "version": recipe["version"]},
        "renderer": renderer,
        "status": "rendered",
        "updated_at": utc_now(),
        "dependencies": dependencies_for_spec(spec),
        "artifacts": {
            "spec": spec_path.name,
            "tex": tex_path.name,
            "pdf": f"{basename}.pdf",
            "manifest": ".funfig/manifest.json",
            "build_dir": ".funfig/build",
        },
        "hashes": {
            "spec_sha256": sha256_file(spec_path),
            "tex_sha256": sha256_file(tex_path),
        },
        "cleanup": {
            "disposable": [".funfig/build/", f"{basename}.pgf-plot.gnuplot", f"{basename}.pgf-plot.table"],
            "preserve": [spec_path.name, tex_path.name, f"{basename}.pdf", "data/"],
        },
    }
    write_manifest(figure_dir, manifest)
    return tex_path, manifest

