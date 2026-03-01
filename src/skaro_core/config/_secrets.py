"""Secrets management: .skaro/secrets.yaml (API keys)."""

from __future__ import annotations

from pathlib import Path

import yaml

from skaro_core.config._models import SECRETS_FILENAME, SKARO_DIR


def _secrets_path(project_root: Path | None = None) -> Path:
    import skaro_core.config as _cfg

    root = project_root or _cfg.find_project_root() or Path.cwd()
    return root / SKARO_DIR / SECRETS_FILENAME


def load_secrets(project_root: Path | None = None) -> dict[str, str]:
    """Load API key secrets from ``.skaro/secrets.yaml``.

    Returns a flat ``{env_name: value}`` dict.
    """
    path = _secrets_path(project_root)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {str(k): str(v) for k, v in (data.get("api_keys") or {}).items()}
    return {}


def save_secret(
    key_name: str, key_value: str, project_root: Path | None = None
) -> Path:
    """Store an API key in ``.skaro/secrets.yaml``.

    Creates the file if it doesn't exist. Merges with existing keys.
    """
    path = _secrets_path(project_root)
    existing: dict[str, str] = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        existing = {str(k): str(v) for k, v in (data.get("api_keys") or {}).items()}

    existing[key_name] = key_value

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            {"api_keys": existing},
            f,
            default_flow_style=False,
            allow_unicode=True,
        )
    return path
