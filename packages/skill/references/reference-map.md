# TIKZ-FunFig reference map

Use this map to find the smallest relevant local reference set before creating a figure.

The legacy paths in this map are **source-repository development references**. They are intentionally excluded from the portable Plugin package. If the source checkout is unavailable, use the bundled Recipe/Schema behavior; do not treat a missing legacy path as a runtime dependency failure.

All paths are relative to the workspace root.

## Toolchain and installation

- `.agents/skills/TIKZ-FunFig/references/dependencies.md` — TeX/latexmk/gnuplot requirements, Homebrew installation, shell-escape notes, and security rules.
- `.agents/skills/TIKZ-FunFig/scripts/check_dependencies.sh` — verify the full local toolchain.
- `.agents/skills/TIKZ-FunFig/scripts/setup_macos.sh` — install missing gnuplot on macOS through Homebrew and then verify the toolchain.
- `.agents/skills/TIKZ-FunFig/scripts/compile_tikz.sh` — compile figures and automatically enable shell escape only for detected gnuplot-backed PGFPlots source.

## 1. Publication-style worked figures

Directory:

`tikz-funfig/references/legacy/publication-sustainability-1485080/`

This is the strongest historical reference for the visual style and structure of research figures in this workspace. It contains 11 figure folders with original `.tex`, lightweight source data, notes, and `generate_data_legacy.py` files extracted from the historical notebooks. Rendered PDF/SVG copies and notebook containers are intentionally excluded from the maintained repository.

Useful examples:

- `fig1/fig1.tex` — 2D PGFPlots figure with shaded regime, multiple curves, manually selected ticks, mathematical legend, emphasized points, and arrow callouts.
- `fig4/fig4.tex` — multiple profit curves, regime shading, named paths, intersection computation, and labeled key points.
- `fig11/fig11.tex` — several related curves, piecewise visual emphasis, and compact annotations.

Use these when the user asks for a paper-ready economics/operations-management style plot.

These three examples are the primary sources for the structured `publication-threshold` recipe. Use that recipe before rebuilding their recurring threshold/regime/callout structure manually.

Scientific golden cases derived from the memo material live under:

- `tikz-funfig/examples/golden/error-bar/` — asymmetric explicit x/y error columns.
- `tikz-funfig/examples/golden/scatter-plot/` — table metadata mapped to scatter color plus colorbar.
- `tikz-funfig/examples/golden/confidence-band/` — named upper/lower paths with fill-between.
- `tikz-funfig/examples/golden/groupplot/` — 2×2 group layout with edge-only labels/ticks.
- `tikz-funfig/examples/golden/surface-plot/` — interpolated Gaussian 3D surface with view and colorbar.
- `tikz-funfig/examples/golden/contour-plot/` — explicit gnuplot-backed contour levels.
- `tikz-funfig/examples/golden/heatmap/` — matrix heatmap using explicit coordinate metadata.
- `tikz-funfig/examples/golden/quiver-field/` — analytic rotational vector field.

Use these golden cases before copying raw memo snippets for the same figure class.

Schema-managed golden reconstructions live at:

- `tikz-funfig/examples/golden/fig1/`
- `tikz-funfig/examples/golden/fig4/`
- `tikz-funfig/examples/golden/fig11/`

Prefer these golden cases when changing the current renderer/Schema because
they are compiled and regression-tested. Use the legacy publication sources
above to understand original intent and provenance.

## 2. PGFPlots fundamentals and parameter recipes

Directory:

`tikz-funfig/references/legacy/pgfplots-memo/`

Key paths:

- `00_基本算子参数/00_base.tex` — basic axis skeleton.
- `00_基本算子参数/01_title.tex` — titles.
- `00_基本算子参数/02_legend.tex` — legends.
- `00_基本算子参数/03_grid.tex` — major/minor grids and 3D axis boxes.
- `00_基本算子参数/04_axis_xylabel.tex` — axis labels.
- `00_基本算子参数/05.1_axis.tex` through `05.4_axis_tick_label.tex` — axis placement, ticks, and tick labels.
- `01_plot/01.1_coordinate.tex` through `01.9_coordinate_bar stacked.tex` — coordinate-based plot variants.
- `01_plot/02.1_table.tex` through `02.7_table_filter.tex` — table-based plotting, labels, dates, filters, errors.
- `01_plot/02.4_table_error.tex` — explicit asymmetric x/y errors.
- `01_plot/03_quiver.tex` — quiver/vector fields.
- `01_plot/04_fillbetween.tex` — fill-between.
- `01_plot/02.3_table_3D.tex` — table-driven 3D surface, shader, and colorbar.
- `coordinate/03_矩阵图.tex` in the extended memo — matrix/heatmap semantics.
- `02_scatter plots/` — marker/scatter recipes.
- `隐函数.tex` — implicit-function experimentation.

Use this directory for syntax lookup and compact plot recipes.

## 3. Extended TikZ and PGFPlots notes

Directory:

`tikz-funfig/references/legacy/tikz-memo/`

### TikZ structure and geometry

- `01_tikz_基础/1.>>环境结构层次/tikzpicture.tex` — environment basics.
- `01_tikz_基础/1.>>环境结构层次/scope.tex` — scoped styles/transforms.
- `01_tikz_基础/1.>>环境结构层次/pgfsetlayers.tex` — foreground/background layers.
- `01_tikz_基础/2.>>坐标系/` — current page/bounding coordinate systems.
- `01_tikz_基础/3.>>算子/路径相交点.tex` — named paths and intersections.
- `01_tikz_基础/3.>>算子/spy.tex` — magnified detail regions.
- `01_tikz_基础/4.>>算子-选项/allset.tex` — broad option memo: shapes, transforms, line styles, joins, arrows, curves, names.
- `01_tikz_基础/4.>>算子-选项/arrows.tex` — arrow-tip variants and custom tips.
- `01_tikz_基础/n-1.>>style设置/tikzset.tex` — reusable TikZ styles.

### PGFPlots

- `02_pgfplots/groupplots.tex` — multi-panel plots with `groupplots`.
- `02_pgfplots/基本设置/03标题.tex` — titles.
- `02_pgfplots/基本设置/03网格线.tex` — grids.
- `02_pgfplots/基本设置/04坐标轴.tex` — axis positioning/direction/shift.
- `02_pgfplots/基本设置/05轴标题.tex` — axis titles.
- `02_pgfplots/基本设置/06轴_数值刻度.tex` and neighboring files — ticks and labels.
- `02_pgfplots/基本设置/07图例.tex` — legend placement and alignment.
- `02_pgfplots/基本设置/08.1colorbar.tex`, `08.2colorbar.tex` — colorbars.
- `02_pgfplots/coordinate/` — coordinate plots, stacked plots, matrix plots, jumps, labeled scatter, metadata scatter.
- `02_pgfplots/table/` — table columns, expressions, labels, dates, filters, meta/scatter, error bars, surfaces, colorbars.
- `02_pgfplots/table/08_误差棒.tex` — multi-panel error-bar examples.
- `02_pgfplots/fill between/` — filling between named paths, soft clipping, segmented fills.

### Data ingestion

- `读取csv/1csvreader读取表.tex`
- `读取csv/2csvset设定样式.tex`
- `读取csv/3autotable.tex`
- `读取csv/grade.csv`, `grade2.csv`

### LaTeX/PGF programming

- `00_latex_宏命令基础/02控制序列/foreach.tex` — loops, evaluate, remember, break.
- `00_latex_宏命令基础/03宏命令/pgfmathparse.tex` — PGF math parsing.
- `00_latex_宏命令基础/03宏命令/pgfmathsetmacro.tex` — computed macros.
- `00_latex_宏命令基础/03宏命令/xparse.tex` — structured custom commands.
- `00_latex_宏命令基础/变量/` — counters, conditionals, pgfkeys, globals.

### Chinese typesetting

- `中文/xeCJK.tex` — XeLaTeX + xeCJK example.
- `中文/CJKutf8.tex` — legacy UTF-8/CJK route.

Prefer XeLaTeX for new figures containing Chinese text.

## 4. Local helper styles

- `tikz-funfig/references/legacy/tikz-memo/iitikz.sty` — broader helper setup, custom `\iiplot`, coordinate extraction, annotation helpers.
- `tikz-funfig/references/legacy/pgfplots-memo/itikz.sty` — package/library bundle and basic plotting defaults.
- `tikz-funfig/references/legacy/pgfplots-memo/icommand.tex` — custom commands used by the memo package.

Do not blindly import these helper files into new work. Read the relevant definitions and copy only the minimal, valid abstractions needed by the new figure.

The `\iiplot` helper depends on `raw gnuplot`. The current workspace toolchain includes gnuplot; still run the dependency check when moving the skill to another machine.

