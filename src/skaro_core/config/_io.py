"""Config I/O: project root discovery, load/save config.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

from skaro_core.config._models import (
    CONFIG_FILENAME,
    GLOBAL_CONFIG_DIR,
    SKARO_DIR,
    SkaroConfig,
)


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up from start (or cwd) looking for .skaro/ directory.

    Skips directories where .skaro/ is the global installation directory
    (venv, bin) rather than a project directory.
    """
    current = start or Path.cwd()
    global_dir = GLOBAL_CONFIG_DIR.resolve()
    for parent in [current, *current.parents]:
        candidate = parent / SKARO_DIR
        if candidate.is_dir() and candidate.resolve() != global_dir:
            return parent
    return None


def skaro_path(project_root: Path | None = None) -> Path:
    """Return the .skaro/ directory path."""
    root = project_root or find_project_root()
    if root is None:
        return Path.cwd() / SKARO_DIR
    return root / SKARO_DIR


def load_config(project_root: Path | None = None) -> SkaroConfig:
    """Load config from .skaro/config.yaml, falling back to global then defaults."""
    root = project_root or find_project_root()
    if root:
        project_config = root / SKARO_DIR / CONFIG_FILENAME
        if project_config.exists():
            with open(project_config, encoding="utf-8") as f:
                return SkaroConfig.from_dict(yaml.safe_load(f) or {})

    global_config = GLOBAL_CONFIG_DIR / CONFIG_FILENAME
    if global_config.exists():
        with open(global_config, encoding="utf-8") as f:
            return SkaroConfig.from_dict(yaml.safe_load(f) or {})

    return SkaroConfig()


def save_config(config: SkaroConfig, project_root: Path | None = None) -> Path:
    """Save config to .skaro/config.yaml.

    Only env-var **names** are persisted — never actual API key values.
    """
    root = project_root or find_project_root() or Path.cwd()
    config_path = root / SKARO_DIR / CONFIG_FILENAME
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)
    return config_path
