from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .io import write_text_atomic
from .manifest import sha256_file, utc_now, write_manifest
from .recipes import load_recipe
from .schema import validate_spec


PUBLICATION_OFFSET_RECIPES = {
    "implicit-function",
    "function-plot",
    "data-series",
    "error-bar",
    "scatter-plot",
    "confidence-band",
    "threshold-region",
    "intersection-curves",
    "publication-threshold",
    "groupplot",
}
DEFAULT_PUBLICATION_AXIS_SHIFT = "6.5pt"


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
    preset = axes.get("preset")
    if preset is None:
        preset = (
            "publication-offset"
            if spec.get("recipe") in PUBLICATION_OFFSET_RECIPES
            else "standard"
        )
    if preset == "publication-offset":
        options.append(
            f"axis line shift={axes.get('axis_line_shift', DEFAULT_PUBLICATION_AXIS_SHIFT)}"
        )
    elif axes.get("axis_line_shift"):
        # Explicit shift remains a supported low-level override even when the
        # standard preset is selected.
        options.append(f"axis line shift={axes['axis_line_shift']}")

    grid = axes.get("grid", "major")
    if grid != "none":
        options.append(f"grid={grid}")
        options.append("grid style={gray!25,line width=0.2pt}")

    if axes.get("title"):
        options.append(f"title={{{axes['title']}}}")
        options.append("title style={align=left}")
    if axes.get("tick_precision") is not None:
        options.append(
            "ticklabel style={/pgf/number format/precision="
            f"{int(axes['tick_precision'])}" + "}"
        )

    view = axes.get("view") or {}
    if view:
        options.append(
            f"view={{{_fmt(view['azimuth'])}}}{{{_fmt(view['elevation'])}}}"
        )
    if axes.get("box3d"):
        options.append(f"3d box={axes['box3d']}")
    if axes.get("colormap"):
        options.append(f"colormap/{axes['colormap']}")

    colorbar = axes.get("colorbar") or {}
    if colorbar:
        position = colorbar.get("position", "right")
        if position == "left":
            options.append("colorbar left")
        elif position == "horizontal":
            options.append("colorbar horizontal")
        else:
            options.append("colorbar")
        if colorbar.get("label"):
            label_key = "xlabel" if position == "horizontal" else "ylabel"
            options.append(f"colorbar style={{{label_key}={{{colorbar['label']}}}}}")

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


def _plot_mode(series: dict[str, Any]) -> dict[str, Any]:
    value = series.get("plot")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return {"kind": value}
    if series.get("scatter"):
        return {"kind": "scatter"}
    return {"kind": "line"}


def _gnuplot_expression(source: dict[str, Any]) -> str:
    """Return a gnuplot expression for an implicit source.

    Historical TIKZ-FunFig helpers accepted a mathematical equation and
    plotted its zero contour. Preserve that semantic contract here instead of
    requiring callers to hand-write raw gnuplot every time.
    """
    raw = str(source.get("equation") or source.get("expression") or "").strip()
    if "=" in raw:
        lhs, rhs = raw.split("=", 1)
        raw = f"({lhs.strip()})-({rhs.strip()})"
    # PGF math examples commonly use ^, while gnuplot exponentiation is **.
    return raw.replace("^", "**")


def _axis_range(axes: dict[str, Any], key: str, fallback: str) -> str:
    axis = (axes or {}).get(key) or {}
    if axis.get("min") is not None and axis.get("max") is not None:
        return f"{_fmt(axis['min'])}:{_fmt(axis['max'])}"
    return fallback


def _implicit_gnuplot_script(source: dict[str, Any], axes: dict[str, Any]) -> str:
    xrange = source.get("domain") or _axis_range(axes, "x", "-5:5")
    yrange = source.get("y_domain") or _axis_range(axes, "y", "-5:5")
    level = _fmt(source.get("level", 0))
    samples = int(source.get("samples", 100))
    isosamples = int(source.get("isosamples", samples))
    expression = _gnuplot_expression(source)
    return "\n".join(
        [
            f"set xrange [{xrange}];",
            f"set yrange [{yrange}];",
            "set contour;",
            "unset surface;",
            "set view map;",
            f"set cntrparam levels discrete {level};",
            f"set isosamples {isosamples};",
            f"set samples {samples};",
            f"splot {expression};",
        ]
    )


def _series_path_decorations(
    series: dict[str, Any], annotations: list[dict[str, Any]] | None
) -> list[str]:
    result: list[str] = []
    for index, annotation in enumerate(annotations or [], start=1):
        if annotation.get("series") != series.get("id"):
            continue
        kind = annotation.get("type")
        position = annotation.get("position")
        if kind == "curve_probe":
            name = annotation.get("name", f"funfigProbe{index}")
            result.append(f"coordinate[pos={_fmt(position)}] ({name})")
        elif kind == "curve_label":
            node_options = [f"pos={_fmt(position)}"]
            if annotation.get("sloped", True):
                node_options.append("sloped")
            if annotation.get("anchor"):
                node_options.append(f"anchor={annotation['anchor']}")
            if annotation.get("font"):
                node_options.append(f"font={annotation['font']}")
            node_options.extend(_style_options(annotation.get("style")))
            result.append(
                f"node[{','.join(node_options)}] {{{annotation.get('label', '')}}}"
            )
    return result


def _coordinate_formatter(ref: str, show: str, precision: int) -> str:
    formatter = {
        "x": "funfigcoordx",
        "y": "funfigcoordy",
        "xy": "funfigcoordxy",
    }.get(show, "funfigcoordxy")
    return f"\\{formatter}{{{ref}}}{{{precision}}}"


def _coordinate_label(annotation: dict[str, Any], ref: str) -> str:
    precision = int(annotation.get("precision", 2))
    show = annotation.get("show", "xy")
    explicit = annotation.get("label")
    if isinstance(explicit, str):
        return explicit

    template = annotation.get("template")
    if isinstance(template, str):
        result = template
        replacements = {
            "{x}": _coordinate_formatter(ref, "x", precision),
            "{y}": _coordinate_formatter(ref, "y", precision),
            "{xy}": _coordinate_formatter(ref, "xy", precision),
            "{ref}": ref,
        }
        for token, replacement in replacements.items():
            result = result.replace(token, replacement)
        return result

    return annotation.get("label_prefix", "") + _coordinate_formatter(ref, show, precision)


def _error_bar_options(error_bars: dict[str, Any] | None) -> tuple[list[str], list[str]]:
    if not error_bars:
        return [], []
    plot_options = ["error bars/.cd"]
    table_options: list[str] = []
    for axis in ("x", "y"):
        config = error_bars.get(axis)
        if not config:
            continue
        mode = config.get("mode", "explicit")
        plot_options.append(f"{axis} dir={config.get('dir', 'none')}")
        if mode == "explicit":
            plot_options.append(f"{axis} explicit")
        elif mode == "explicit_relative":
            plot_options.append(f"{axis} explicit relative")
        elif mode == "fixed":
            plot_options.append(f"{axis} fixed={_fmt(config['value'])}")
        elif mode == "fixed_relative":
            plot_options.append(f"{axis} fixed relative={_fmt(config['value'])}")

        if config.get("column"):
            table_options.append(f"{axis} error={config['column']}")
        if config.get("plus"):
            table_options.append(f"{axis} error plus={config['plus']}")
        if config.get("minus"):
            table_options.append(f"{axis} error minus={config['minus']}")
        if config.get("expr"):
            table_options.append(f"{axis} error expr={config['expr']}")
    if error_bars.get("mark"):
        plot_options.append(f"error mark={error_bars['mark']}")
    if error_bars.get("style"):
        plot_options.append(f"error bar style={{{','.join(error_bars['style'])}}}")
    return plot_options, table_options


def _render_series(
    series: dict[str, Any],
    source: dict[str, Any],
    axes: dict[str, Any] | None = None,
    annotations: list[dict[str, Any]] | None = None,
) -> list[str]:
    options = _style_options(series.get("style"))
    plot_mode = _plot_mode(series)
    plot_kind = plot_mode.get("kind", "line")
    scatter = series.get("scatter") or {}
    is_scatter = plot_kind == "scatter" or bool(scatter)
    if is_scatter:
        options.extend(["scatter", "only marks"])
        if scatter.get("source"):
            options.append(f"scatter src={scatter['source']}")
        if scatter.get("point_meta"):
            options.append(f"point meta={scatter['point_meta']}")
        if scatter.get("nodes_near_coords"):
            options.append("nodes near coords")
    elif plot_kind == "line":
        # Do not inherit PGFPlots' cycle-list marker by accident. A FunFig
        # series is a line by default; markers are opt-in through style.mark.
        if not any(option.startswith("mark=") for option in options):
            options.append("mark=none")

    if plot_kind in {"surface", "mesh", "heatmap", "contour", "quiver"}:
        if not any(option.startswith("mark=") for option in options):
            options.append("mark=none")

    if plot_kind == "surface":
        options.append("surf")
    elif plot_kind == "mesh":
        options.append("mesh")
    elif plot_kind == "heatmap":
        options.extend(["matrix plot*", "point meta=explicit"])
    elif plot_kind == "contour":
        levels = ",".join(_fmt(level) for level in (plot_mode.get("levels") or []))
        options.append(f"contour gnuplot={{levels={{{levels}}}}}")
    elif plot_kind == "quiver":
        quiver_parts = [
            f"u={{{plot_mode['u']}}}",
            f"v={{{plot_mode['v']}}}",
        ]
        if plot_mode.get("w") is not None:
            quiver_parts.append(f"w={{{plot_mode['w']}}}")
        if plot_mode.get("scale_arrows") is not None:
            quiver_parts.append(f"scale arrows={_fmt(plot_mode['scale_arrows'])}")
        options.append(f"quiver={{{','.join(quiver_parts)}}}")
        options.extend(plot_mode.get("arrow_style", []) or [])

    if plot_mode.get("shader"):
        options.append(f"shader={plot_mode['shader']}")
    if plot_mode.get("mesh_rows"):
        options.append(f"mesh/rows={int(plot_mode['mesh_rows'])}")
    if plot_mode.get("mesh_cols"):
        options.append(f"mesh/cols={int(plot_mode['mesh_cols'])}")
    if plot_mode.get("point_meta"):
        options.append(f"point meta={plot_mode['point_meta']}")
    options.extend(series.get("options", []) or [])
    if series.get("name_path"):
        options.append(f"name path={series['name_path']}")
    error_options, error_table_options = _error_bar_options(series.get("error_bars"))
    options.extend(error_options)

    source_type = source["type"]
    if source_type != "implicit" and source.get("domain"):
        options.append(f"domain={source['domain']}")
    if source_type != "implicit" and source.get("y_domain"):
        options.append(f"y domain={source['y_domain']}")
    if source_type != "implicit" and source.get("samples"):
        options.append(f"samples={source['samples']}")

    bracket = f"[{','.join(options)}]" if options else ""
    is_3d = plot_kind in {"surface", "mesh", "contour", "quiver"}
    if source_type == "function":
        command = "\\addplot3+" if is_3d else "\\addplot+"
        plot = f"{command} {bracket} {{{source['expression']}}};"
    elif source_type == "file":
        columns = []
        for key in ("x", "y", "z"):
            if source.get(key):
                columns.append(f"{key}={source[key]}")
        if is_scatter and scatter.get("meta"):
            columns.append(f"meta={scatter['meta']}")
        if plot_kind == "heatmap" and plot_mode.get("point_meta"):
            columns.append(f"meta={plot_mode['point_meta']}")
        columns.extend(error_table_options)
        table_options = f"[{','.join(columns)}]" if columns else ""
        command = "\\addplot3" if ((source.get("z") and plot_kind != "heatmap") or is_3d) else "\\addplot+"
        plot = f"{command} {bracket} table{table_options} {{{source['path']}}};"
    elif source_type == "coordinates":
        if plot_kind == "heatmap":
            points = " ".join(
                f"({_fmt(point[0])},{_fmt(point[1])}) [{_fmt(point[2])}]"
                for point in source.get("points", [])
            )
            plot = f"\\addplot+ {bracket} coordinates {{{points}}};"
        else:
            points = " ".join(
                "(" + ",".join(_fmt(value) for value in point) + ")"
                for point in source.get("points", [])
            )
            command = "\\addplot3+" if is_3d else "\\addplot+"
            plot = f"{command} {bracket} coordinates {{{points}}};"
    elif source_type == "gnuplot":
        gp_options = ",".join(options)
        gp_bracket = f"[{gp_options}]" if gp_options else ""
        plot = f"\\addplot+ gnuplot{gp_bracket} {{{source['expression']}}};"
    elif source_type == "raw_gnuplot":
        gp_options = ["raw gnuplot"] + options
        plot = f"\\addplot+ gnuplot[{','.join(gp_options)}] {{\n{source['script']}\n}};"
    elif source_type == "implicit":
        gp_options = ["raw gnuplot", "empty line=jump"] + options
        script = _implicit_gnuplot_script(source, axes or {})
        plot = f"\\addplot+ gnuplot[{','.join(gp_options)}] {{\n{script}\n}};"
    else:
        raise ValueError(f"unsupported data source type: {source_type}")

    decorations = _series_path_decorations(series, annotations)
    if decorations:
        plot = plot.rstrip().removesuffix(";") + " " + " ".join(decorations) + ";"

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
            names = annotation.get("names")
            if isinstance(names, list) and names:
                intersection_names = [str(name) for name in names]
                by_value = "{" + ",".join(intersection_names) + "}"
            else:
                intersection_names = [annotation.get("name", f"intersection{index}")]
                by_value = intersection_names[0]
            lines.append(
                f"\\path[name intersections={{of={annotation['path_a']} and {annotation['path_b']},by={by_value}}}];"
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
            labels = annotation.get("labels") if isinstance(annotation.get("labels"), list) else []
            for name_index, name in enumerate(intersection_names):
                lines.append(f"\\draw[{','.join(marker_draw)}] ({name}) circle (0.7mm);")
                label = labels[name_index] if name_index < len(labels) else (
                    annotation.get("label") if name_index == 0 else None
                )
                if not label:
                    continue
                anchor = annotation.get("anchor", "south west")
                shift = annotation.get("shift", "(2pt,2pt)")
                node_name = (
                    f"funfigIntersectionCallout{index}"
                    if len(intersection_names) == 1
                    else f"funfigIntersectionCallout{index}_{name_index + 1}"
                )
                node_options = [f"anchor={anchor}"]
                if annotation.get("font"):
                    node_options.append(f"font={annotation['font']}")
                lines.append(
                    f"\\node[{','.join(node_options)}] ({node_name}) at "
                    f"([shift={{{shift}}}]{name}) {{{label}}};"
                )
                if annotation.get("arrow"):
                    arrow_options = annotation.get("arrow_style") or ["-{Stealth[length=4pt,width=3pt]}", "shorten >=1pt"]
                    arrow_anchor = annotation.get("arrow_anchor", "center")
                    lines.append(
                        f"\\draw[{','.join(arrow_options)}] ({node_name}.{arrow_anchor}) -- ({name});"
                    )
        elif kind == "curve_probe":
            name = annotation.get("name", f"funfigProbe{index}")
            raw_style = annotation.get("style") or {}
            if annotation.get("marker", True):
                marker_options = []
                if raw_style.get("fill"):
                    marker_options.append(f"fill={raw_style['fill']}")
                if raw_style.get("draw"):
                    marker_options.append(f"draw={raw_style['draw']}")
                elif raw_style.get("color"):
                    marker_options.append(f"draw={raw_style['color']}")
                if not marker_options:
                    marker_options.extend(["fill=white", "draw=black"])
                marker_options.append("line width=0.45pt")
                lines.append(f"\\draw[{','.join(marker_options)}] ({name}) circle (0.75mm);")
            if annotation.get("label", True):
                label = _coordinate_label(annotation, name)
                pin_angle = annotation.get("pin_angle")
                if pin_angle is not None:
                    pin_options = []
                    if annotation.get("font"):
                        pin_options.append(f"font={annotation['font']}")
                    pin_style = f"[{','.join(pin_options)}]" if pin_options else ""
                    lines.append(
                        f"\\node[inner sep=0pt,pin={{{pin_style}{_fmt(pin_angle)}:{{{label}}}}}] at ({name}) {{}};"
                    )
                    continue
                anchor = annotation.get("anchor", "south west")
                shift = annotation.get("shift", "(3pt,3pt)")
                node_options = [f"anchor={anchor}"]
                if annotation.get("font"):
                    node_options.append(f"font={annotation['font']}")
                lines.append(
                    f"\\node[{','.join(node_options)}] at ([shift={{{shift}}}]{name}) {{{label}}};"
                )
        elif kind == "coordinate_ref":
            ref = annotation["ref"]
            label = _coordinate_label(annotation, ref)
            anchor = annotation.get("anchor", "south west")
            shift = annotation.get("shift", "(3pt,3pt)")
            node_options = [f"anchor={anchor}"]
            if annotation.get("font"):
                node_options.append(f"font={annotation['font']}")
            lines.append(
                f"\\node[{','.join(node_options)}] at ([shift={{{shift}}}]{ref}) {{{label}}};"
            )
        elif kind == "curve_label":
            # Rendered as part of the plot path so it tracks curve geometry.
            continue
        elif kind == "spy":
            x, y = annotation["at"]
            in_x, in_y = annotation["in"]
            on_name = f"funfigSpyOn{index}"
            in_name = f"funfigSpyIn{index}"
            lines.append(
                f"\\coordinate ({on_name}) at (axis cs:{_fmt(x)},{_fmt(y)});"
            )
            lines.append(
                f"\\coordinate ({in_name}) at (axis cs:{_fmt(in_x)},{_fmt(in_y)});"
            )
            spy_options = [annotation.get("shape", "rectangle")]
            spy_options.append(f"magnification={_fmt(annotation.get('magnification', 4))}")
            if annotation.get("size"):
                spy_options.append(f"size={annotation['size']}")
            else:
                if annotation.get("width"):
                    spy_options.append(f"width={annotation['width']}")
                if annotation.get("height"):
                    spy_options.append(f"height={annotation['height']}")
            if annotation.get("connect", True):
                spy_options.append("connect spies")
            spy_options.extend(style)
            lines.append(
                f"\\spy[{','.join(spy_options)}] on ({on_name}) in node at ({in_name});"
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
    if any(
        annotation.get("type") == "spy"
        for annotation in spec.get("annotations", [])
        if isinstance(annotation, dict)
    ):
        lines.append("\\usetikzlibrary{spy}")
    needs_coordinate_helpers = any(
        annotation.get("type") in {"curve_probe", "coordinate_ref"}
        for annotation in spec.get("annotations", [])
        if isinstance(annotation, dict)
    )
    if needs_coordinate_helpers:
        lines.extend(
            [
                "\\newcommand{\\funfigcoordx}[2]{%",
                "  \\pgfplotspointgetcoordinates{(#1)}%",
                "  \\ensuremath{\\pgfmathprintnumber[fixed,precision=#2]{\\pgfkeysvalueof{/data point/x}}}%",
                "}",
                "\\newcommand{\\funfigcoordy}[2]{%",
                "  \\pgfplotspointgetcoordinates{(#1)}%",
                "  \\ensuremath{\\pgfmathprintnumber[fixed,precision=#2]{\\pgfkeysvalueof{/data point/y}}}%",
                "}",
                "\\newcommand{\\funfigcoordxy}[2]{%",
                "  \\pgfplotspointgetcoordinates{(#1)}%",
                "  \\ensuremath{(\\pgfmathprintnumber[fixed,precision=#2]{\\pgfkeysvalueof{/data point/x}},\\pgfmathprintnumber[fixed,precision=#2]{\\pgfkeysvalueof{/data point/y}})}%",
                "}",
            ]
        )
    if groupplots:
        lines.append("\\usepgfplotslibrary{groupplots}")
    return lines


def render_pgfplots(spec: dict[str, Any]) -> str:
    sources = _source_map(spec)
    lines = _document_preamble(spec)
    has_spy = any(
        annotation.get("type") == "spy"
        for annotation in spec.get("annotations", [])
        if isinstance(annotation, dict)
    )
    tikzpicture = (
        "\\begin{tikzpicture}[spy using outlines={rectangle,magnification=4,size=2cm}]"
        if has_spy
        else "\\begin{tikzpicture}"
    )
    lines += ["", "\\begin{document}", tikzpicture]
    axis_options = _axis_options(spec)
    lines.append("\\begin{axis}[")
    lines.extend(f"  {option}," for option in axis_options)
    lines.append("]")

    lines.extend(_render_regions(spec, between=False))
    for series in spec.get("series", []):
        lines.extend(
            _render_series(
                series,
                sources[series["source"]],
                spec.get("axes") or {},
                spec.get("annotations") or [],
            )
        )
    lines.extend(_render_regions(spec, between=True))
    lines.extend(_render_annotations(spec))
    lines += ["\\end{axis}", "\\end{tikzpicture}", "\\end{document}", ""]
    return "\n".join(lines)


def render_groupplot(spec: dict[str, Any]) -> str:
    sources = _source_map(spec)
    series_by_id = _series_map(spec)
    panels = spec.get("panels", [])
    group = spec.get("group") or {}
    columns = int(group.get("columns", (spec.get("metadata") or {}).get("group_columns", min(2, max(1, len(panels))))))
    rows = max(1, math.ceil(len(panels) / columns))
    lines = _document_preamble(spec, groupplots=True)
    lines += ["", "\\begin{document}", "\\begin{tikzpicture}"]
    lines.append("\\begin{groupplot}[")
    group_style = [
        f"group size={columns} by {rows}",
        f"horizontal sep={group.get('horizontal_sep', '1.5cm')}",
        f"vertical sep={group.get('vertical_sep', '1.2cm')}",
    ]
    for key in ("xticklabels_at", "yticklabels_at", "xlabels_at", "ylabels_at"):
        if group.get(key):
            group_style.append(f"{key.replace('_', ' ')}={{{group[key]}}}")
    lines.append(f"  group style={{{','.join(group_style)}}},")
    for option in _axis_options(spec):
        lines.append(f"  {option},")
    lines.append("]")

    for panel in panels:
        panel_options = []
        if panel.get("title"):
            panel_options.append(f"title={{{panel['title']}}}")
        # Global axis settings already live on the groupplot container. Do not
        # copy them into every panel, otherwise PGFPlots' edge-only label/tick
        # rules are defeated. Only emit panel axes when the panel explicitly
        # declares an override.
        if panel.get("axes"):
            panel_options.extend(_axis_options(spec, panel["axes"]))
        lines.append(f"\\nextgroupplot[{','.join(panel_options)}]")
        for series_id in panel.get("series", []):
            series = series_by_id[series_id]
            lines.extend(
                _render_series(
                    series,
                    sources[series["source"]],
                    panel.get("axes") or spec.get("axes") or {},
                    spec.get("annotations") or [],
                )
            )

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
    plot_kinds = {_plot_mode(series).get("kind") for series in spec.get("series", [])}
    needs_gnuplot = bool(source_types & {"gnuplot", "raw_gnuplot", "implicit"}) or "contour" in plot_kinds or (
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
            "disposable": [
                ".funfig/build/",
                f"{basename}.pgf-plot.gnuplot",
                f"{basename}.pgf-plot.table",
                f"{basename}_contourtmp*",
            ],
            "preserve": [spec_path.name, tex_path.name, f"{basename}.pdf", "data/"],
        },
    }
    write_manifest(figure_dir, manifest)
    return tex_path, manifest

