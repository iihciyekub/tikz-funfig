# Codex Installation, Update, and Rollback

The canonical Codex marketplace is `tikz-funfig`, backed by the private Git repository:

```text
git@github.com:iihciyekub/tikz-funfig.git
```

A machine must have GitHub SSH access to that repository.

## First install

Without cloning the repository:

```bash
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref main
codex plugin add tikz-funfig@tikz-funfig
```

With a local checkout, install the helper and Plugin:

```bash
./scripts/install_codex.sh
```

This installs `tff` in `~/.local/bin` when possible.

## Normal updates

```bash
tff update
```

This refreshes/replaces the configured Git marketplace as necessary, installs the newest marketplace Plugin version, and runs the installed dependency doctor.

Useful commands:

```bash
tff status
tff doctor
```

## What Codex installs

Installed versions live under:

```text
~/.codex/plugins/cache/tikz-funfig/tikz-funfig/<version>/
```

Do not edit cache contents. Changes belong in the Git repository and must be released normally.

## Rollback

The supported rollback unit is a published Git tag. Do not mutate a cached installed version.

For a temporary rollback, reconfigure the marketplace to the required tag and reinstall:

```bash
codex plugin remove tikz-funfig@tikz-funfig || true
codex plugin marketplace remove tikz-funfig || true
codex plugin marketplace add git@github.com:iihciyekub/tikz-funfig.git --ref v0.8.2
codex plugin add tikz-funfig@tikz-funfig
```

Return to normal updates by replacing the marketplace with `--ref main` or running the current repository's installer/update helper.

