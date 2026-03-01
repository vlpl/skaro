"""Helper utilities for the artifacts package."""

from __future__ import annotations

from pathlib import Path


def _find_templates_dir() -> Path | None:
    """Locate bundled templates directory.

    Tries ``importlib.resources`` first (works for pip-installed packages),
    then falls back to relative path resolution (works in development).
    Returns ``None`` if templates cannot be found.
    """
    try:
        from importlib.resources import files  # Python 3.9+

        pkg_templates = files("skaro_core") / "templates"
        if pkg_templates.is_dir():  # type: ignore[union-attr]
            return Path(str(pkg_templates))
    except (ImportError, ModuleNotFoundError, TypeError):
        pass

    dev_path = Path(__file__).parent.parent.parent.parent / "templates"
    if dev_path.is_dir():
        return dev_path

    return None


TEMPLATES_PKG_DIR: Path | None = _find_templates_dir()
