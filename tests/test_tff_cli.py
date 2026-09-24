from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import re

from funfig import __version__

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("tff_cli", str(ROOT / "scripts/tff"))
spec = importlib.util.spec_from_loader(loader.name, loader)
tff = importlib.util.module_from_spec(spec)
loader.exec_module(tff)

MARKET = "tikz-funfig"
GIT_MARKET = {"name": MARKET, "marketplaceSource": {"sourceType": "git", "source": "ssh://example/repo"}}
RECORD = {"pluginId": f"{MARKET}@{MARKET}", "installed": True, "enabled": True, "version": "0.8.4"}


class TffCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tff cli ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def test_versions_and_bundled_helper_match(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        canonical = re.search(r'(?m)^version\s*=\s*"([^"]+)"$', pyproject)
        self.assertIsNotNone(canonical)
        self.assertEqual(canonical.group(1), __version__)
        self.assertEqual(tff.VERSION, __version__)
        self.assertEqual((ROOT / "scripts/tff").read_bytes(),
                         (ROOT / "packages/plugin/tikz-funfig/scripts/tff").read_bytes())

    def test_first_install_registers_then_verifies_enabled_plugin(self):
        responses = [
            {"marketplaces": []}, {}, {"marketplaces": [GIT_MARKET]}, {},
            {"installed": [RECORD]},
        ]
        with patch.object(tff, "codex", side_effect=responses) as cli, \
             patch.object(tff, "installed_root", return_value=self.root), \
             patch.object(tff, "refresh_helper"), patch.object(tff, "doctor") as doctor, \
             patch.dict(os.environ, {"TFF_MARKETPLACE_SOURCE": "ssh://example/repo", "TFF_MARKETPLACE_REF": "v0.8.4"}):
            self.assertEqual(tff.install_or_update(MARKET, MARKET, True), 0)
            self.assertIn(unittest.mock.call("plugin", "marketplace", "add", "ssh://example/repo", "--ref", "v0.8.4"), cli.call_args_list)
            self.assertIn(unittest.mock.call("plugin", "add", f"{MARKET}@{MARKET}"), cli.call_args_list)
            doctor.assert_not_called()

    def test_failed_refresh_never_removes_or_reinstalls(self):
        with patch.object(tff, "codex", side_effect=[{"marketplaces": [GIT_MARKET]}, tff.CliError("network unavailable")]) as cli:
            with self.assertRaisesRegex(tff.CliError, "network unavailable"):
                tff.install_or_update(MARKET, MARKET)
            self.assertEqual(cli.call_count, 2)
            self.assertEqual(cli.call_args.args, ("plugin", "marketplace", "upgrade", MARKET))

    def test_update_preserves_configured_source_and_ref(self):
        with patch.object(tff, "codex", side_effect=[{"marketplaces": [GIT_MARKET]}, {}, {}, {"installed": [RECORD]}]) as cli, \
             patch.object(tff, "installed_root", return_value=self.root), \
             patch.object(tff, "refresh_helper"), patch.object(tff, "doctor", return_value=0):
            self.assertEqual(tff.install_or_update(MARKET, MARKET), 0)
            self.assertNotIn("add", cli.call_args_list[1].args)
            self.assertFalse(any("--ref" in call.args for call in cli.call_args_list))
            self.assertFalse(any("remove" in call.args for call in cli.call_args_list))

    def test_local_marketplace_is_not_destroyed(self):
        local = {"name": MARKET, "marketplaceSource": {"sourceType": "local"}}
        with patch.object(tff, "codex", return_value={"marketplaces": [local]}) as cli:
            with self.assertRaisesRegex(tff.CliError, "not Git-backed"):
                tff.install_or_update(MARKET, MARKET)
            self.assertEqual(cli.call_count, 1)

    def test_dependency_failure_distinguishes_successful_install(self):
        with patch.object(tff, "codex", side_effect=[{"marketplaces": [GIT_MARKET]}, {}, {}, {"installed": [RECORD]}]), \
             patch.object(tff, "installed_root", return_value=self.root), \
             patch.object(tff, "refresh_helper"), patch.object(tff, "doctor", return_value=1), \
             contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(tff.install_or_update(MARKET, MARKET), 3)
            self.assertIn("installation succeeded", errors.getvalue())

    def test_recorded_version_wins_over_stale_newer_cache(self):
        with patch.object(tff.os, "environ", {}), patch.object(tff.Path, "home", return_value=self.root):
            cache = self.root / ".codex/plugins/cache" / MARKET / MARKET
            for version in ["0.8.4", "9.9.9"]:
                folder = cache / version
                folder.mkdir(parents=True)
                (folder / "plugin.json").write_text(json.dumps({"name": MARKET, "version": version}))
            self.assertEqual(tff.installed_root(RECORD, MARKET, MARKET), cache / "0.8.4")
            (cache / "0.8.4/plugin.json").unlink()
            with self.assertRaisesRegex(tff.CliError, "cache is missing"):
                tff.installed_root(RECORD, MARKET, MARKET)

    def test_codex_home_override_and_manifest_identity(self):
        cache = self.root / "plugins/cache" / MARKET / MARKET / "0.8.4"
        cache.mkdir(parents=True)
        manifest = cache / "plugin.json"
        with patch.object(tff.os, "environ", {"CODEX_HOME": str(self.root)}):
            manifest.write_text(json.dumps({"name": MARKET, "version": "0.8.4"}))
            self.assertEqual(tff.installed_root(RECORD, MARKET, MARKET), cache)
            manifest.write_text(json.dumps({"name": MARKET, "version": "9.9.9"}))
            with self.assertRaisesRegex(tff.CliError, "mismatch"):
                tff.installed_root(RECORD, MARKET, MARKET)

    def test_upgrade_alias_and_invalid_args(self):
        with patch.object(tff, "install_or_update", return_value=0) as install:
            self.assertEqual(tff.main(["upgrade", "--skip-doctor"]), 0)
            install.assert_called_once_with(MARKET, MARKET, True)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            tff.main(["update", "unexpected"])
        self.assertEqual(error.exception.code, 2)

    def test_helper_only_setup_with_spaces_never_needs_codex(self):
        bin_dir = self.root / "helper bin"
        result = subprocess.run(
            ["bash", str(ROOT / "scripts/install_codex.sh"), "--cli-only"],
            env={**os.environ, "TFF_BIN_DIR": str(bin_dir)}, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((bin_dir / "tff").read_bytes(), (ROOT / "scripts/tff").read_bytes())
        self.assertTrue(os.access(bin_dir / "tff", os.X_OK))
        self.assertFalse(list(bin_dir.glob(".tff-*")))

    def test_helper_refresh_only_replaces_installed_helper(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        target = bin_dir / "tff"
        target.write_text("old")
        bundled = self.root / "plugin/scripts"
        bundled.mkdir(parents=True)
        (bundled / "tff").write_text("new")
        with patch.dict(os.environ, {"TFF_BIN_DIR": str(bin_dir)}):
            tff.refresh_helper(self.root / "plugin")
            self.assertEqual(target.read_text(), "old")
            with patch.object(tff, "__file__", str(target)):
                tff.refresh_helper(self.root / "plugin")
            self.assertEqual(target.read_text(), "new")
            self.assertTrue(os.access(target, os.X_OK))

    def test_missing_plugin_does_not_use_stale_cache(self):
        with self.assertRaisesRegex(tff.CliError, "not installed"):
            tff.installed_root(None, MARKET, MARKET)

    def test_malformed_codex_response_is_not_treated_as_first_install(self):
        with patch.object(tff, "codex", return_value={"unexpected": []}) as cli:
            with self.assertRaisesRegex(tff.CliError, "Unsupported Codex response"):
                tff.install_or_update(MARKET, MARKET)
            self.assertEqual(cli.call_count, 1)


if __name__ == "__main__":
    unittest.main()
