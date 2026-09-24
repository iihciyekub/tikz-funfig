# Codex Installation, Update, and Rollback

The `tff` CLI installs and updates the `tikz-funfig@tikz-funfig` Codex Plugin.
It uses Codex's supported plugin commands and does not edit Codex configuration
or installed cache files by hand.

## Quick start

With this repository already available, run from its root:

```bash
./scripts/install_codex.sh
```

This installs the standalone CLI into `~/.local/bin/tff`, installs/enables the
Plugin from the configured Git marketplace, and checks drawing dependencies.
The CLI needs Python 3.9 or newer; the full drawing runtime declares Python 3.10+
and additionally needs TeX/latexmk (and gnuplot for relevant recipes).

Then use these commands from any directory with `~/.local/bin` on `PATH`:

```bash
tff install          # First installation, or reinstall/update an existing Plugin
tff update           # Normal updates
tff upgrade          # Alias of update
tff status           # Actual installed Plugin version, source, enabled state, cache
tff doctor           # Check drawing dependencies
tff --version        # CLI version (separate from the installed Plugin version)
```

For unpublished local development, do not use `tff update`: it fetches the
configured Git marketplace. Instead, synchronize the portable bundle and add
the current repository as a local marketplace:

```bash
./scripts/sync_plugin_package.sh
codex plugin marketplace add "$(pwd)"
codex plugin add tikz-funfig@tikz-funfig
```

See [CODEX_PLUGIN.md](CODEX_PLUGIN.md) for the full local/Git/release/publication
workflow.

On a new machine, with Git, Python and Codex CLI already installed, this one-line
command obtains the repository and runs the installer (choose an unused destination):

```bash
git clone --depth 1 git@github.com:iihciyekub/tikz-funfig.git "$HOME/tikz-funfig" && "$HOME/tikz-funfig/scripts/install_codex.sh"
```

The repository is private, so the machine needs GitHub SSH access. Do not use an
unauthenticated public `curl` download for this repository. These Git-based
commands obtain committed remote content; a locally edited version becomes
available to other machines only after it has been published.

If `~/.local/bin` is not on `PATH`, the installer prints the full CLI path. Use
`~/.local/bin/tff` directly, or add this to your shell configuration:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

The installer does not rewrite your shell configuration.

## Installer options

```bash
./scripts/install_codex.sh --cli-only       # Install/refresh the CLI without changing Codex
./scripts/install_codex.sh --skip-doctor    # Install Plugin without checking TeX dependencies
tff install --skip-doctor
tff update --skip-doctor
```

The helper remains installed if Plugin installation fails, so after correcting
SSH access or the Codex CLI setup, retry with `tff install`.

After a successful Plugin update, an installed `~/.local/bin/tff` refreshes itself
from the Plugin's bundled helper, if present. A CLI run directly from a source
checkout does not replace itself. Older Plugin versions without a bundled helper
leave the CLI unchanged. `scripts/update_codex.sh` first installs the current
checkout's helper, avoiding stale executables on `PATH`.

Exit code `0` means the operation completed; `1` means a configuration, Codex or
cache error; `2` means invalid command arguments. Installation returning `3`
means the Plugin was installed successfully but its drawing dependency check
failed. `tff doctor` itself returns the underlying doctor's exit code.

## Marketplace behavior

The default source for a first installation is:

```text
git@github.com:iihciyekub/tikz-funfig.git
```

It initially tracks `main`. For an already configured Git marketplace, `install`
and `update` refresh that source and **preserve its configured ref**. An update
failure is reported without attempting to remove the marketplace or installed
Plugin. Re-running installation is supported.

A local marketplace using the same name is not silently replaced. To deliberately
switch it to the canonical Git source, inspect `codex plugin marketplace list
--json`, then explicitly remove that marketplace registration and add the Git source:

```bash
codex plugin marketplace remove tikz-funfig
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref main
tff install
```

There is no need to uninstall the Plugin first. Remove the historical
`tikz-funfig-local` registration only if you deliberately want to retire it;
ordinary updates do not remove unrelated or legacy installations automatically.

The following environment overrides are supported:

| Variable | Effect |
| --- | --- |
| `TFF_BIN_DIR` | Helper installation directory; defaults to `~/.local/bin` |
| `TFF_MARKETPLACE` | Marketplace name; defaults to `tikz-funfig` |
| `TFF_PLUGIN` | Plugin name; defaults to `tikz-funfig` |
| `TFF_MARKETPLACE_SOURCE` | Git source when registering a missing marketplace |
| `TFF_MARKETPLACE_REF` | Git ref when registering a missing marketplace; defaults to `main` |
| `CODEX_HOME` | Codex's existing home override, also respected for installed-cache lookup |

Source/ref overrides do not change an already configured marketplace. Reconfigure
it explicitly through Codex when intentionally changing branches or rolling back.
For a custom `TFF_BIN_DIR`, use the same override during updates so CLI refresh
can identify the intended installation path.

## Installed versions

The CLI uses the version returned by `codex plugin list --json`, not whichever
cache directory sorts highest. This matters after a rollback or interrupted update.
The default cache path is:

```text
~/.codex/plugins/cache/tikz-funfig/tikz-funfig/<installed-version>/
```

A missing or mismatched installed manifest is reported as an error. Do not edit
cache contents. Start a new Codex task after installation/update so it can load
the updated Skills; a running task may retain its previous instructions.

## Rollback

The rollback unit is a published immutable Git tag. To select a previous version:

```bash
codex plugin marketplace remove tikz-funfig
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref v0.8.4
tff install
```

Normal updates continue following that pinned tag. To resume `main` updates:

```bash
codex plugin marketplace remove tikz-funfig
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref main
tff update
```

## Development and publication

Bumping local version files and synchronizing the portable package prepares a
version; it does not publish a Git release or update other machines. Follow
[the release workflow](RELEASE.md) after reviewing and committing changes and
passing the required checks.

Codex command details were checked against the installed CLI's `--help` and the
[official marketplace documentation](https://developers.openai.com/plugins/build/plugins).
