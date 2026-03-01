"""Dev plan mixin: CRUD for devplan.md."""

from __future__ import annotations

import shutil
from pathlib import Path


class DevplanMixin:
    """Manages .skaro/devplan.md."""

    @property
    def devplan_path(self) -> Path:
        return self.skaro / "devplan.md"

    @property
    def has_devplan(self) -> bool:
        if not self.devplan_path.exists():
            return False
        content = self.devplan_path.read_text(encoding="utf-8")
        if self._is_template_content(content, "devplan-template.md"):
            return False
        return bool(content.strip())

    def read_devplan(self) -> str:
        if self.devplan_path.exists():
            return self.devplan_path.read_text(encoding="utf-8")
        return ""

    def write_devplan(self, content: str) -> Path:
        self.devplan_path.write_text(content, encoding="utf-8")
        return self.devplan_path

    def create_devplan(self) -> Path:
        template = self.skaro / "templates" / "devplan-template.md"
        if template.exists():
            shutil.copy2(template, self.devplan_path)
        else:
            self.devplan_path.write_text(
                "# Development Plan\n\n<!-- Fill in your development plan -->\n",
                encoding="utf-8",
            )
        return self.devplan_path
