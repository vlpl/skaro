"""Hatch build hook: builds Svelte frontend before packaging."""

import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class FrontendBuildHook(BuildHookInterface):
    PLUGIN_NAME = 'frontend-build'

    def initialize(self, version, build_data):
        frontend_dir = Path(self.root) / 'frontend'
        static_dir = Path(self.root) / 'src' / 'skaro_web' / 'static'

        if not frontend_dir.exists():
            return

        # Skip if static already has fresh build (e.g. CI pre-built)
        index_html = static_dir / 'index.html'
        package_json = frontend_dir / 'package.json'
        if index_html.exists() and index_html.stat().st_mtime > package_json.stat().st_mtime:
            return

        self._run('npm install', frontend_dir)
        self._run('npm run build', frontend_dir)

    def _run(self, cmd, cwd):
        print(f'[frontend-build] Running: {cmd}')
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            raise RuntimeError(f'[frontend-build] Failed: {cmd}')
