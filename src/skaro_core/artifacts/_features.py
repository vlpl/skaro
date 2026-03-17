"""Features mixin: CRUD for .skaro/features/{slug}/ entities."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


class FeaturesMixin:
    """Manages .skaro/features/ — feature directories with meta, plan, conversation."""

    @property
    def features_dir(self) -> Path:
        return self.skaro / "features"

    def feature_dir(self, slug: str) -> Path:
        return self.features_dir / slug

    def feature_exists(self, slug: str) -> bool:
        return (self.feature_dir(slug) / "meta.json").exists()

    # ── CRUD ────────────────────────────────────

    def create_feature(self, *, title: str = "", description: str = "") -> str:
        """Create a new feature with auto-incremented slug. Returns slug."""
        self.features_dir.mkdir(parents=True, exist_ok=True)

        # Determine next number
        existing = self._list_feature_dirs()
        max_num = 0
        for name in existing:
            if name.startswith("feat-"):
                try:
                    num = int(name.split("-", 1)[1])
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    pass
        slug = f"feat-{max_num + 1:02d}"

        fdir = self.feature_dir(slug)
        fdir.mkdir(parents=True, exist_ok=True)

        meta = {
            "title": title,
            "slug": slug,
            "description": description,
            "status": "draft",
            "tasks": [],
            "adrs": [],
            "created_at": date.today().isoformat(),
            "updated_at": date.today().isoformat(),
        }
        self._write_feature_meta(slug, meta)
        return slug

    def delete_feature(self, slug: str) -> bool:
        """Delete a draft feature from disk. Returns False if not draft or not found."""
        meta = self.read_feature_meta(slug)
        if not meta:
            return False
        if meta.get("status") != "draft":
            return False
        import shutil
        shutil.rmtree(self.feature_dir(slug), ignore_errors=True)
        return True

    def cancel_feature(self, slug: str) -> bool:
        """Cancel a non-draft feature (mark as cancelled). Returns False if not found."""
        meta = self.read_feature_meta(slug)
        if not meta:
            return False
        if meta.get("status") == "draft":
            return False
        meta["status"] = "cancelled"
        meta["updated_at"] = date.today().isoformat()
        self._write_feature_meta(slug, meta)
        return True

    # ── Meta ────────────────────────────────────

    def read_feature_meta(self, slug: str) -> dict[str, Any] | None:
        path = self.feature_dir(slug) / "meta.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def _write_feature_meta(self, slug: str, meta: dict[str, Any]) -> Path:
        path = self.feature_dir(slug) / "meta.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def update_feature_meta(self, slug: str, **updates: Any) -> dict[str, Any] | None:
        """Update specific fields in meta.json. Returns updated meta or None."""
        meta = self.read_feature_meta(slug)
        if meta is None:
            return None
        meta.update(updates)
        meta["updated_at"] = date.today().isoformat()
        self._write_feature_meta(slug, meta)
        return meta

    def update_feature_status(self, slug: str, new_status: str) -> bool:
        """Update feature status. Returns False if not found."""
        valid = {"draft", "planned", "in-progress", "done", "cancelled"}
        if new_status not in valid:
            return False
        meta = self.read_feature_meta(slug)
        if meta is None:
            return False
        meta["status"] = new_status
        meta["updated_at"] = date.today().isoformat()
        self._write_feature_meta(slug, meta)
        return True

    # ── Plan ────────────────────────────────────

    def read_feature_plan(self, slug: str) -> str:
        path = self.feature_dir(slug) / "plan.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write_feature_plan(self, slug: str, content: str) -> Path:
        path = self.feature_dir(slug) / "plan.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    # ── Conversation ────────────────────────────

    def feature_conversation_path(self, slug: str) -> Path:
        return self.feature_dir(slug) / "conversation.json"

    def feature_log_path(self, slug: str) -> Path:
        return self.feature_dir(slug) / "log.md"

    # ── Listing ─────────────────────────────────

    def _list_feature_dirs(self) -> list[str]:
        if not self.features_dir.is_dir():
            return []
        return sorted(
            d.name
            for d in self.features_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        )

    def list_features(self) -> list[dict[str, Any]]:
        """Return list of feature summaries for UI."""
        result = []
        for slug in self._list_feature_dirs():
            meta = self.read_feature_meta(slug)
            if meta:
                result.append(meta)
        return result

    def list_features_count(self) -> int:
        return len(self._list_feature_dirs())

    # ── Auto-status ─────────────────────────────

    def refresh_feature_status(self, slug: str) -> str | None:
        """Recompute feature status based on linked task states.

        - planned → in-progress: at least one task in progress
        - in-progress → done: all tasks complete

        Returns new status or None if unchanged/not applicable.
        """
        meta = self.read_feature_meta(slug)
        if not meta:
            return None

        current = meta.get("status", "draft")
        if current not in ("planned", "in-progress"):
            return None

        task_slugs = meta.get("tasks", [])
        if not task_slugs:
            return None

        states = []
        for task_slug in task_slugs:
            resolved = self.resolve_task_safe(task_slug)
            if resolved:
                ts = self.get_task_state(*resolved)
                states.append(ts)

        if not states:
            return None

        all_done = all(s.progress_percent == 100 for s in states)
        any_in_progress = any(
            s.progress_percent > 0 and s.progress_percent < 100
            for s in states
        )

        new_status = current
        if current == "planned" and (any_in_progress or all_done):
            new_status = "in-progress"
        if current == "in-progress" and all_done:
            new_status = "done"

        if new_status != current:
            self.update_feature_status(slug, new_status)
            return new_status

        return None

    # ── Task linking ────────────────────────────

    def link_task_to_feature(self, slug: str, task_slug: str) -> bool:
        meta = self.read_feature_meta(slug)
        if not meta:
            return False
        tasks = meta.get("tasks", [])
        if task_slug not in tasks:
            tasks.append(task_slug)
            meta["tasks"] = tasks
            meta["updated_at"] = date.today().isoformat()
            self._write_feature_meta(slug, meta)
        return True

    def link_adr_to_feature(self, slug: str, adr_number: int) -> bool:
        meta = self.read_feature_meta(slug)
        if not meta:
            return False
        adrs = meta.get("adrs", [])
        if adr_number not in adrs:
            adrs.append(adr_number)
            meta["adrs"] = adrs
            meta["updated_at"] = date.today().isoformat()
            self._write_feature_meta(slug, meta)
        return True
