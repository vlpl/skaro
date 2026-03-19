"""Constitution mixin: CRUD + validation for constitution.md."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


class ConstitutionMixin:
    """Manages .skaro/constitution.md."""

    @property
    def constitution_path(self) -> Path:
        return self.skaro / "constitution.md"

    @property
    def has_constitution(self) -> bool:
        if not self.constitution_path.exists():
            return False
        content = self.constitution_path.read_text(encoding="utf-8")
        if self._is_template_content(content, "constitution-template.md"):
            return False
        return bool(content.strip())

    def create_constitution(self) -> Path:
        template = self.skaro / "templates" / "constitution-template.md"
        if template.exists():
            shutil.copy2(template, self.constitution_path)
        else:
            self.constitution_path.write_text(
                "# Constitution\n\n<!-- Fill in your project principles -->\n",
                encoding="utf-8",
            )
        return self.constitution_path

    def read_constitution(self) -> str:
        if self.constitution_path.exists():
            return self.constitution_path.read_text(encoding="utf-8")
        return ""

    def write_constitution(self, content: str) -> Path:
        self.constitution_path.parent.mkdir(parents=True, exist_ok=True)
        self.constitution_path.write_text(content, encoding="utf-8")
        return self.constitution_path

    def validate_constitution(self) -> dict[str, bool]:
        """Validate Constitution sections (bilingual support)."""
        content = self.read_constitution().lower()
        return {
            "stack": any(
                w in content
                for w in [
                    "## stack",
                    "стек",
                    "technology stack",
                    "технологический стек",
                    "language:",
                    "язык:",
                ]
            ),
            "coding_standards": any(
                w in content
                for w in [
                    "## coding",
                    "стандарты",
                    "coding standards",
                    "стандарты разработки",
                    "linter",
                    "линтер",
                    "formatter",
                    "форматтер",
                ]
            ),
            "testing": any(
                w in content
                for w in [
                    "## testing",
                    "тестирование",
                    "coverage",
                    "покрытие",
                    "test requirements",
                    "требования к тестированию",
                ]
            ),
            "constraints": any(
                w in content
                for w in [
                    "## constraints",
                    "ограничения",
                    "constraints and infrastructure",
                    "инфраструктура",
                    "infra",
                    "инфра",
                ]
            ),
            "security": any(
                w in content
                for w in [
                    "## security",
                    "безопасность",
                    "authorization",
                    "авторизация",
                    "authentication",
                    "аутентификация",
                ]
            ),
            "llm_rules": any(
                w in content
                for w in [
                    "## llm",
                    "llm rules",
                    "правила работы с llm",
                    "llm usage",
                    "использование llm",
                    "stub",
                    "заглушк",
                    "ai_notes",
                ]
            ),
        }
