# TIKZ-FunFig dependencies

## Required commands

The complete local workflow expects these commands on `PATH`:

```text
latexmk
pdflatex
xelatex
gnuplot
```

`pdflatex` handles most standalone TikZ/PGFPlots figures. `xelatex` is preferred when the figure contains Chinese text or requires system/OpenType fonts. `latexmk` manages repeat compilation. `gnuplot` is required for PGFPlots `gnuplot` and `raw gnuplot` handlers, including the implicit-function workflow used by the local `\iiplot` helper.

## macOS installation

### gnuplot

Homebrew is the supported installation route:

```bash
brew install gnuplot
```

Then verify:

```bash
command -v gnuplot
gnuplot --version
```

On Apple Silicon with the default Homebrew prefix, the executable is normally reachable under `/opt/homebrew/bin/gnuplot`, but scripts should rely on `PATH` rather than hard-coding that location.

### TeX toolchain

If the TeX commands are missing, install a suitable TeX Live/MacTeX distribution. This skill does not silently install a full TeX distribution because it is large and may be managed separately by the user.

Check everything at once with:

```bash
.agents/skills/TIKZ-FunFig/scripts/check_dependencies.sh
```

The macOS setup helper installs only missing Homebrew-manageable dependencies:

```bash
.agents/skills/TIKZ-FunFig/scripts/setup_macos.sh
```

## Why PGFPlots needs shell escape for gnuplot

PGFPlots can delegate a plot calculation to the external `gnuplot` executable. TeX must therefore be allowed to launch that process. For a trusted source, the equivalent manual compile is:

```bash
latexmk -pdf -latexoption=-shell-escape figure.tex
```

For XeLaTeX:

```bash
latexmk -xelatex -latexoption=-shell-escape figure.tex
```

The bundled `compile_tikz.sh` detects gnuplot-backed source and adds this option automatically.

## Security rule

`-shell-escape` expands TeX's capabilities beyond ordinary document compilation. Never enable it blindly for an unknown or untrusted `.tex` file. Before compiling third-party source, inspect it for commands or packages that execute external programs.

TIKZ-FunFig-generated or locally reviewed source may use shell escape when gnuplot is required.

