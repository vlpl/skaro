"""Fix phase: conversational bug fixing within a task context.

Provides LLM with full project context (spec, plan, AI_NOTES, source files)
and maintains a conversation log in fix-log.md.

Each fix request sends the full conversation history so LLM can iterate.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from skaro_core.llm.base import LLMMessage
from skaro_core.phases.base import BasePhase, PhaseResult

FIX_LOG_FILENAME = "fix-log.md"


class FixPhase(BasePhase):
    phase_name = "fix"

    async def run(self, task: str | None = None, **kwargs: Any) -> PhaseResult:
        """Process a fix request within task context.

        kwargs:
            message: str — user's bug description / follow-up
            conversation: list[dict] — previous conversation turns
                [{"role": "user"|"assistant", "content": "..."}]
        """
        if not task:
            return PhaseResult(success=False, message="Task name is required.")

        user_message: str = kwargs.get("message", "")
        conversation: list[dict] = kwargs.get("conversation", [])

        if not user_message.strip():
            return PhaseResult(success=False, message="Message is required.")

        # ── Build rich context ──
        extra_context = await asyncio.to_thread(self._gather_context, task)

        # ── Build system prompt ──
        system = self._build_system_message()
        system += (
            "\n\n# YOUR ROLE\n"
            "You are a senior developer fixing bugs and issues in this project.\n"
            "The user will describe a problem they found. You must:\n"
            "1. Analyze the issue using the project context provided\n"
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

        # ── Build messages list ──
        messages = [LLMMessage(role="system", content=system)]

        # Add context as initial exchange
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

        # Add conversation history
        for turn in conversation:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content.strip():
                messages.append(LLMMessage(role=role, content=content))

        # Add current user message
        final_message = user_message
        if self.config.lang != "en":
            final_message += f"\n\n---\nReminder: {self._lang_instruction()}"
        messages.append(LLMMessage(role="user", content=final_message))

        # ── Call LLM (streaming to avoid timeout on large context) ──
        response_content = await self._stream_collect(messages, min_tokens=16384, task=task or "")

        # ── Parse file changes from response ──
        proposed_files = self._parse_file_blocks(response_content)

        # ── Read current content of proposed files for diff ──
        file_diffs = {}
        for fpath, new_content in proposed_files.items():
            old_content = self._read_project_file(fpath)
            file_diffs[fpath] = {
                "old": old_content,
                "new": new_content,
                "is_new": old_content is None,
            }

        # ── Build updated conversation ──
        updated_conversation = list(conversation) + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response_content},
        ]

        # ── Persist ──
        self._append_fix_log(task, user_message, response_content, proposed_files)
        self._save_conversation(task, updated_conversation)

        return PhaseResult(
            success=True,
            message=response_content,
            data={
                "files": file_diffs,
                "conversation": updated_conversation,
            },
        )

    def load_conversation(self, task: str) -> list[dict]:
        """Load persisted conversation from JSON file."""
        conv_path = self.artifacts.find_task_dir(task) / "fix-conversation.json"
        if conv_path.exists():
            try:
                return json.loads(conv_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def clear_conversation(self, task: str) -> None:
        """Clear persisted conversation."""
        conv_path = self.artifacts.find_task_dir(task) / "fix-conversation.json"
        if conv_path.exists():
            conv_path.unlink()

    def apply_file(self, task: str, filepath: str, content: str) -> PhaseResult:
        """Apply a single proposed file change to disk."""
        try:
            target = self._validate_project_path(self.artifacts.root, filepath)
        except ValueError as e:
            return PhaseResult(success=False, message=str(e))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        # Log the application
        self._append_apply_log(task, filepath)

        return PhaseResult(
            success=True,
            message=f"Applied: {filepath}",
            artifacts_updated=[filepath],
        )

    # ── Context gathering ──

    def _gather_context(self, task: str) -> dict[str, str]:
        """Collect all relevant context for the LLM."""
        ctx: dict[str, str] = {}

        # Architecture
        arch = self.artifacts.read_architecture()
        if arch.strip():
            ctx["Architecture"] = arch

        # Feature spec
        spec = self.artifacts.find_and_read_task_file(task, "spec.md")
        if spec:
            ctx["Task Specification"] = spec

        # Clarifications
        clarif = self.artifacts.find_and_read_task_file(task, "clarifications.md")
        if clarif:
            ctx["Clarifications"] = clarif

        # Plan
        plan = self.artifacts.find_and_read_task_file(task, "plan.md")
        if plan:
            ctx["Implementation Plan"] = plan

        # All AI_NOTES from completed stages
        completed = self.artifacts.find_completed_stages(task)
        for s in sorted(completed):
            notes_path = self.artifacts.find_stage_dir(task, s) / "AI_NOTES.md"
            if notes_path.exists():
                ctx[f"Stage {s} AI_NOTES"] = notes_path.read_text(encoding="utf-8")

        # Source files from the whole project
        source_files = self._collect_project_sources(max_files=30, max_file_size=15_000)
        if source_files:
            parts = []
            for fpath, content in source_files.items():
                parts.append(f"### {fpath}\n```\n{content}\n```")
            ctx["Current Project Source Files"] = "\n\n".join(parts)

        # Project tree
        tree = self._scan_project_tree()
        if tree:
            ctx["Project File Tree"] = tree

        return ctx

    def _read_project_file(self, filepath: str) -> str | None:
        """Read a file from the project root. Returns None if not found."""
        target = self.artifacts.root / filepath
        if target.is_file():
            try:
                return target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                return None
        return None

    # ── Fix log persistence ──

    def _save_conversation(self, task: str, conversation: list[dict]) -> None:
        """Save full conversation (with file diffs) as JSON."""
        conv_path = self.artifacts.find_task_dir(task) / "fix-conversation.json"
        conv_path.parent.mkdir(parents=True, exist_ok=True)
        conv_path.write_text(json.dumps(conversation, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_fix_log(
        self, task: str, user_msg: str, llm_msg: str, files: dict[str, str]
    ) -> None:
        """Append a fix exchange to fix-log.md."""
        existing = self.artifacts.find_and_read_task_file(task, FIX_LOG_FILENAME) or ""
        if not existing.strip():
            existing = f"# Fix Log: {task}\n"

        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        file_list = ", ".join(f"`{f}`" for f in files.keys()) if files else "(no files)"

        entry = (
            f"\n---\n\n"
            f"## {ts}\n\n"
            f"**User:** {user_msg}\n\n"
            f"**LLM:** {llm_msg[:500]}{'...' if len(llm_msg) > 500 else ''}\n\n"
            f"**Proposed files:** {file_list}\n"
        )

        self.artifacts.find_and_write_task_file(
            task, FIX_LOG_FILENAME, existing + entry
        )

    def _append_apply_log(self, task: str, filepath: str) -> None:
        """Append an apply note to fix-log.md."""
        existing = self.artifacts.find_and_read_task_file(task, FIX_LOG_FILENAME) or ""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing += f"\n**Applied:** `{filepath}` ✓ ({ts})\n"
        self.artifacts.find_and_write_task_file(task, FIX_LOG_FILENAME, existing)
