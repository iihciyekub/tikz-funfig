# Codex Plugin Packaging, Installation, and Publication

TIKZ-FunFig is packaged as a portable Codex/OpenAI Plugin. The canonical
Plugin bundle is generated at:

```text
packages/plugin/tikz-funfig/
```

It contains the six TIKZ-FunFig Skills, the dependency-light runtime snapshot,
schemas, Recipes, searchable knowledge, curated Templates, themes, Publication
Profiles, and Plugin assets. Raw upstream source trees under `sources/` are
development/provenance inputs and are not distributed.

## 1. Build the portable Plugin

From the repository root:

```bash
python3 scripts/version.py check
./scripts/sync_plugin_package.sh
python3 scripts/check_plugin_bundle.py
```

For a release-quality build, run the complete regression suite:

```bash
./scripts/check.sh
```

The generated root manifest is:

```text
packages/plugin/tikz-funfig/plugin.json
```

The repository marketplace catalog is:

```text
.agents/plugins/marketplace.json
```

The marketplace name and Plugin name are both `tikz-funfig`, so the selector
is:

```text
tikz-funfig@tikz-funfig
```

## 2. Install the current local checkout into Codex

Use this path while developing unpublished changes. First build/sync the
portable bundle, then register the repository root as a local marketplace:

```bash
./scripts/sync_plugin_package.sh
codex plugin marketplace add "$(pwd)"
codex plugin add tikz-funfig@tikz-funfig
```

Verify what Codex can see:

```bash
codex plugin marketplace list
codex plugin list --marketplace tikz-funfig --available
```

After changing the local Plugin, synchronize the bundle again and refresh the
local installation from the Plugin browser or re-add/update the local
marketplace as appropriate. Start a new Codex task after changing Skills so the
new instructions are loaded.

If a Git-backed marketplace named `tikz-funfig` is already configured, do
not silently replace it. Inspect the existing source first:

```bash
codex plugin marketplace list
```

Switch sources deliberately by removing that marketplace registration and
adding the desired local or Git source.

## 3. Install from the private Git repository

For normal private distribution, publish the repository to GitHub and register
it as a Git marketplace:

```bash
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref main
codex plugin add tikz-funfig@tikz-funfig
```

The repository is private, so the machine needs GitHub SSH access.

The project helper wraps the same supported Codex commands:

```bash
./scripts/install_codex.sh
```

After the helper is installed in `~/.local/bin/tff`:

```bash
tff install
tff update
tff status
tff doctor
```

`tff install` and `tff update` operate on the configured Git marketplace.
They do not read unpublished working-tree changes.

## 4. Install a specific released version

For reproducible use, prefer an immutable release tag rather than `main`:

```bash
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref v0.10.0
codex plugin add tikz-funfig@tikz-funfig
```

To change an existing marketplace from `main` to a release tag:

```bash
codex plugin marketplace remove tikz-funfig
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref v0.10.0
codex plugin add tikz-funfig@tikz-funfig
```

Use `tff status` or:

```bash
codex plugin list --marketplace tikz-funfig
```

to confirm the installed version.

## 5. Publish a new Git release

Version ownership is centralized:

```text
pyproject.toml              canonical version
src/funfig/__init__.py      derived runtime version
scripts/tff                 derived helper version
plugin.json                 derived Plugin version
```

Check or change it with:

```bash
python3 scripts/version.py get
python3 scripts/version.py check
python3 scripts/version.py set X.Y.Z
```

Before a release, add the matching section to `CHANGELOG.md`, commit normal
development work, and leave the tree clean. Then run:

```bash
./scripts/release.sh X.Y.Z
```

The release script synchronizes versions and the portable Plugin, runs the full
test suite, creates the release commit and immutable annotated `vX.Y.Z` tag,
pushes `main` and the tag, and refreshes the local Codex installation when
available.

## 6. Make the Plugin available to other users

There are three distinct distribution scopes:

### Private Git / team development

Keep using the Git-backed marketplace commands above. This is the simplest
distribution path for a private repository or a small development team.

### ChatGPT workspace

A workspace admin can install the Plugin from a personal/local source and use
the Plugins UI to publish it to selected workspace roles. Workspace publishing
keeps the Plugin inside the organization; it does not list it publicly.

### Universal public Plugins Directory

For public distribution across supported ChatGPT and Codex surfaces, submit
the Plugin through OpenAI's Plugin submission flow after the portable manifest,
publisher metadata, documentation, privacy/security requirements, and install
surface copy are ready.

Submission documentation:
<https://developers.openai.com/plugins/deploy/submission>

TIKZ-FunFig is primarily a local Codex Plugin because compilation depends on
local TeX/latexmk and some Recipes require gnuplot/Poppler. Publishing the
Plugin does not install those native dependencies into a user's machine or a
web-hosted environment. Keep `tff doctor` and the dependency documentation as
part of the installation contract.

## 7. Use it from Codex

After installation, start a new Codex task and describe the figure naturally,
for example:

```text
Use TIKZ-FunFig to draw a journal-quality three-layer research framework.
Use a monochrome publication style and save it under figures/framework-1.
```

or:

```text
Use TIKZ-FunFig to plot this CSV with asymmetric error bars and a publication
profile suitable for a two-column paper.
```

The Plugin routes clear requests to specialized Skills such as
`funfig-plots`, `funfig-frameworks`, or `funfig-schematics`; users do not
need to name a Skill manually for ordinary use.

## 8. Authoritative references

- OpenAI Plugin packaging and marketplace documentation:
  <https://developers.openai.com/plugins/build/plugins>
- TIKZ-FunFig install/update/rollback details:
  [INSTALL_UPDATE.md](INSTALL_UPDATE.md)
- TIKZ-FunFig release policy:
  [RELEASE.md](RELEASE.md)
- Portable bundle contract:
  [PLUGIN_DISTRIBUTION.md](PLUGIN_DISTRIBUTION.md)
