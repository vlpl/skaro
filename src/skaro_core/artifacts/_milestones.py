"""Milestones mixin: CRUD for milestone directories."""

from __future__ import annotations

from pathlib import Path


class MilestonesMixin:
    """Manages .skaro/milestones/<slug>/ directories."""

    @property
    def milestones_dir(self) -> Path:
        return self.skaro / "milestones"

    def milestone_dir(self, milestone: str) -> Path:
        return self.milestones_dir / milestone

    def milestone_exists(self, milestone: str) -> bool:
        return self.milestone_dir(milestone).is_dir()

    def create_milestone(
        self, milestone: str, title: str = "", description: str = ""
    ) -> Path:
        """Create a milestone directory with milestone.md."""
        mdir = self.milestone_dir(milestone)
        mdir.mkdir(parents=True, exist_ok=True)

        md_path = mdir / "milestone.md"
        if not md_path.exists():
            display_title = (
                title or milestone.split("-", 1)[-1].replace("-", " ").title()
            )
            content = (
                f"# {display_title}\n\n"
                f"{description}\n\n"
                "## Completion Criteria\n\n"
                "- [ ] All tasks completed and reviewed\n"
            )
            md_path.write_text(content, encoding="utf-8")

        return mdir

    def list_milestones(self) -> list[str]:
        """Return sorted list of milestone directory names."""
        if self.milestones_dir.is_dir():
            return sorted(
                d.name
                for d in self.milestones_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            )
        return []

    def read_milestone_info(self, milestone: str) -> str:
        md_path = self.milestone_dir(milestone) / "milestone.md"
        if md_path.exists():
            return md_path.read_text(encoding="utf-8")
        return ""

    def write_milestone_info(self, milestone: str, content: str) -> Path:
        md_path = self.milestone_dir(milestone) / "milestone.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(content, encoding="utf-8")
        return md_path
