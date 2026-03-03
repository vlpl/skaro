"""Project Fix phase: conversational bug fixing at the project level.

Provides LLM with project-wide context (constitution, invariants, specs,
AI_NOTES, source files) filtered by user-selected scope (milestones/tasks).
Maintains conversation log in .skaro/docs/project-fix-conversation.json
and appends to .skaro/docs/project-fix-log.md.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from skaro_core.llm.base import LLMMessage
from skaro_core.phases.base import BasePhase, PhaseResult

_FIX_LOG_FILENAME = "project-fix-log.md"
_CONVERSATION_FILENAME = "project-fix-conversation.json"


class ProjectFixPhase(BasePhase):
    phase_name = "project_fix"

    async def run(self, task: str | None = None, **kwargs: Any) -> PhaseResult:
        user_message: str = kwargs.get("message", "")
        conversation: list[dict] = kwargs.get("conversation", [])
        scope_tasks: list[str] = kwargs.get("scope_tasks", [])

        if not user_message.strip():
            return PhaseResult(success=False, message="Message is required.")

        extra_context = await asyncio.to_thread(self._gather_context, scope_tasks)

        system = self._build_system_message()
        system += (
            "\n\n# YOUR ROLE\n"
            "You are a senior developer performing project-wide review and fixes.\n"
            "The user will describe a cross-cutting problem found during project review.\n"
            "You must:\n"
            "1. Analyze the issue using the full project context provided\n"
            "2. Propose specific file changes to fix it\n"
            "3. Explain what you changed and why\n\n"
            "# OUTPUT FORMAT\n"
            "First, explain the issue and your fix approach.\n"
            "Then output EACH changed file using fenced code blocks:\n"
            "```path/to/file.ext\n<full file content>\n```\n\n"
            "IMPORTANT: Output the COMPLETE file content, not just the diff.\n"
            "Include ALL changed files. Use relative paths from project root.\n"
            "If you need to create a new file, use the same format.\n"
            "If no code changes are needed, explain why."
        )

        messages = [LLMMessage(role="system", content=system)]

        if extra_context:
            ctx_parts = []
            for label, content in extra_context.items():
                if content.strip():
                    ctx_parts.append(f"## {label}\n\n{content}")
            if ctx_parts:
                messages.append(
                    LLMMessage(role="user", content="\n\n---\n\n".join(ctx_parts))
                )
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content="I've reviewed the full project context. Ready to help fix issues.",
                    )
                )

        for turn in conversation:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content.strip():
                messages.append(LLMMessage(role=role, content=content))

        final_message = user_message
        if self.config.lang != "en":
            final_message += f"\n\n---\nReminder: {self._lang_instruction()}"
        messages.append(LLMMessage(role="user", content=final_message))

        response_content = await self._stream_collect(messages, min_tokens=16384)

        proposed_files = self._parse_file_blocks(response_content)

        file_diffs = {}
        for fpath, new_content in proposed_files.items():
            old_content = self._read_project_file(fpath)
            file_diffs[fpath] = {
                "old": old_content,
                "new": new_content,
                "is_new": old_content is None,
            }

        updated_conversation = list(conversation) + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response_content},
        ]

        self._append_fix_log(user_message, response_content, proposed_files)
        self._save_conversation(updated_conversation)

        return PhaseResult(
            success=True,
            message=response_content,
            data={
                "files": file_diffs,
                "conversation": updated_conversation,
            },
        )

    def load_conversation(self) -> list[dict]:
        conv_path = self.artifacts.skaro / "docs" / _CONVERSATION_FILENAME
        if conv_path.exists():
            try:
                return json.loads(conv_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def clear_conversation(self) -> None:
        conv_path = self.artifacts.skaro / "docs" / _CONVERSATION_FILENAME
        if conv_path.exists():
            conv_path.unlink()

    def apply_file(self, filepath: str, content: str) -> PhaseResult:
        try:
            target = self._validate_project_path(self.artifacts.root, filepath)
        except ValueError as e:
            return PhaseResult(success=False, message=str(e))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._append_apply_log(filepath)
        return PhaseResult(
            success=True,
            message=f"Applied: {filepath}",
            artifacts_updated=[filepath],
        )

    def _gather_context(self, scope_tasks: list[str]) -> dict[str, str]:
        ctx: dict[str, str] = {}

        arch = self.artifacts.read_architecture()
        if arch.strip():
            ctx["Architecture"] = arch

        state = self.artifacts.get_project_state()
        tasks_to_include = scope_tasks if scope_tasks else [ts.name for ts in state.tasks]

        for task_name in tasks_to_include:
            spec = self.artifacts.find_and_read_task_file(task_name, "spec.md")
            if spec:
                ctx[f"Task '{task_name}' Specification"] = spec

            plan = self.artifacts.find_and_read_task_file(task_name, "plan.md")
            if plan:
                ctx[f"Task '{task_name}' Plan"] = plan

            completed = self.artifacts.find_completed_stages(task_name)
            for s in sorted(completed):
                notes_path = self.artifacts.find_stage_dir(task_name, s) / "AI_NOTES.md"
                if notes_path.exists():
                    notes = notes_path.read_text(encoding="utf-8")
                    if len(notes) > 3000:
                        notes = notes[:3000] + "\n... (truncated)"
                    ctx[f"Task '{task_name}' Stage {s} AI_NOTES"] = notes

        source_files = self._collect_project_sources(max_files=40, max_file_size=15_000)
        if source_files:
            parts = []
            for fpath, content in source_files.items():
                parts.append(f"### {fpath}\n```\n{content}\n```")
            ctx["Current Project Source Files"] = "\n\n".join(parts)

        tree = self._scan_project_tree()
        if tree:
            ctx["Project File Tree"] = tree

        return ctx

    def _read_project_file(self, filepath: str) -> str | None:
        target = self.artifacts.root / filepath
        if target.is_file():
            try:
                return target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                return None
        return None

    def _save_conversation(self, conversation: list[dict]) -> None:
        docs_dir = self.artifacts.skaro / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        conv_path = docs_dir / _CONVERSATION_FILENAME
        conv_path.write_text(
            json.dumps(conversation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _append_fix_log(
        self, user_msg: str, llm_msg: str, files: dict[str, str]
    ) -> None:
        docs_dir = self.artifacts.skaro / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        log_path = docs_dir / _FIX_LOG_FILENAME

        existing = ""
        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")
        if not existing.strip():
            existing = "# Project Fix Log\n"

        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        file_list = ", ".join(f"`{f}`" for f in files.keys()) if files else "(no files)"

        entry = (
            f"\n---\n\n"
            f"## {ts}\n\n"
            f"**User:** {user_msg}\n\n"
            f"**LLM:** {llm_msg[:500]}{'...' if len(llm_msg) > 500 else ''}\n\n"
            f"**Proposed files:** {file_list}\n"
        )

        log_path.write_text(existing + entry, encoding="utf-8")

    def _append_apply_log(self, filepath: str) -> None:
        docs_dir = self.artifacts.skaro / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        log_path = docs_dir / _FIX_LOG_FILENAME

        existing = ""
        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")

        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing += f"\n**Applied:** `{filepath}` ({ts})\n"
        log_path.write_text(existing, encoding="utf-8")
