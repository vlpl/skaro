"""Shared pytest fixtures for Skaro test suite."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from skaro_core.artifacts import ArtifactManager


@pytest.fixture
def project_dir():
    """Temporary project directory, cleaned up after test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def am(project_dir):
    """Initialized ArtifactManager with a temp project."""
    manager = ArtifactManager(project_dir)
    manager.init_project()
    return manager


@pytest.fixture
def project_with_files(project_dir):
    """Project directory pre-populated with sample source files."""
    src = project_dir / "src" / "myapp"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "main.py").write_text("def main():\n    print('hello')\n", encoding="utf-8")
    (src / "utils.py").write_text("def helper():\n    return 42\n", encoding="utf-8")
    # File that should be skipped
    pycache = project_dir / "src" / "myapp" / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-312.pyc").write_bytes(b"\x00")
    return project_dir
