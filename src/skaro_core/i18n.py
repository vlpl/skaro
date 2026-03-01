"""Internationalization support for Skaro."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_LOCALES_DIR = Path(__file__).parent / "locales"
_current_locale: str = "en"
_strings: dict[str, str] = {}


def set_locale(locale: str) -> None:
    """Set the active locale and load its strings."""
    global _current_locale, _strings
    locale_file = _LOCALES_DIR / f"{locale}.yaml"
    if not locale_file.exists():
        locale_file = _LOCALES_DIR / "en.yaml"
        locale = "en"
    _current_locale = locale
    with open(locale_file, encoding="utf-8") as f:
        _strings = _flatten_dict(yaml.safe_load(f) or {})


def get_locale() -> str:
    """Return the current locale code."""
    return _current_locale


def t(key: str, **kwargs: Any) -> str:
    """Translate a key, with optional format parameters.

    Usage:
        t("cli.init.success", project="my-app")
    """
    if not _strings:
        set_locale(os.environ.get("SKARO_LANG", "en"))
    text = _strings.get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict[str, str]:
    """Flatten nested dict into dot-separated keys."""
    items: list[tuple[str, str]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, str(v)))
    return dict(items)
