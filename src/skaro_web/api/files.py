"""File browsing endpoints for scope selection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from skaro_core.phases.base import SKIP_DIRS, SKIP_BINARY_EXTENSIONS
from skaro_web.api.deps import get_project_root

router = APIRouter(prefix="/api/files", tags=["files"])

# Extensions to always skip (binary, compiled, media, archives)
_SKIP_EXTENSIONS: set[str] = SKIP_BINARY_EXTENSIONS | {
    ".whl", ".tar", ".gz", ".zip", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".bmp",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".exe", ".dll", ".bin", ".o", ".a", ".lib",
    ".sqlite", ".db", ".sqlite3",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".DS_Store",
}

# Files to always skip by exact name
_SKIP_NAMES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "uv.lock",
    ".gitignore", ".gitattributes",
    "LICENSE", "LICENSE.md", "LICENSE.txt",
}

# Extensionless files commonly found in projects
_KNOWN_EXTENSIONLESS: set[str] = {
    "Dockerfile", "Makefile", "Procfile", "Vagrantfile",
    "Gemfile", "Rakefile", "Brewfile", "Justfile",
    ".env", ".env.example", ".env.local", ".env.production",
    ".editorconfig", ".eslintrc", ".prettierrc", ".babelrc",
    ".dockerignore", ".slugignore", ".helmignore",
}

# Maximum file size to include (skip huge generated files)
_MAX_FILE_SIZE = 512_000  # 500 KB


def _build_tree(root: Path) -> list[dict[str, Any]]:
    """Build a nested file tree structure for the project.

    Includes all text/config files relevant to development.
    Skips binary files, lock files, and known junk directories.
    """
    return _scan_dir(root, root)


def _scan_dir(directory: Path, root: Path) -> list[dict[str, Any]]:
    """Recursively scan a directory, returning tree nodes."""
    items: list[dict[str, Any]] = []

    try:
        entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except (PermissionError, OSError):
        return items

    for entry in entries:
        name = entry.name

        if entry.is_dir():
            if name in SKIP_DIRS or name.startswith("."):
                continue
            children = _scan_dir(entry, root)
            if children:
                rel = str(entry.relative_to(root)).replace("\\", "/")
                items.append({
                    "name": name,
                    "path": rel,
                    "type": "dir",
                    "children": children,
                })
        elif entry.is_file():
            if name in _SKIP_NAMES:
                continue
            if entry.suffix.lower() in _SKIP_EXTENSIONS:
                continue
            try:
                size = entry.stat().st_size
            except OSError:
                size = 0
            if size > _MAX_FILE_SIZE:
                continue
            # Skip extensionless files that aren't known and look binary
            if not entry.suffix and name not in _KNOWN_EXTENSIONLESS:
                if not _is_likely_text(entry):
                    continue
            rel = str(entry.relative_to(root)).replace("\\", "/")
            items.append({
                "name": name,
                "path": rel,
                "type": "file",
                "ext": entry.suffix or "",
                "size": size,
            })

    return items


def _is_likely_text(path: Path) -> bool:
    """Quick heuristic: read first 512 bytes and check for null bytes."""
    try:
        chunk = path.read_bytes()[:512]
        return b"\x00" not in chunk
    except (OSError, PermissionError):
        return False


@router.get("/tree")
async def get_file_tree(
    project_root: Path = Depends(get_project_root),
) -> dict[str, Any]:
    """Return the project file tree for scope selection.

    Includes all text/config files relevant to development.
    Skips binary files, lock files, hidden dirs, and known junk.
    """
    tree = _build_tree(project_root)
    return {"tree": tree}
