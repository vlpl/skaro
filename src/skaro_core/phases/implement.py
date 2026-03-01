"""Implement phase: generate code for a single stage."""

from __future__ import annotations

import re
from typing import Any, AsyncIterator

from skaro_core.phases.base import BasePhase, PhaseResult


class ImplementPhase(BasePhase):
    phase_name = "implement"

    async def run(self, task: str | None = None, **kwargs: Any) -> PhaseResult:
        if not task:
            return PhaseResult(success=False, message="Task name is required.")

        stage: int | None = kwargs.get("stage")
        source_files: dict[str, str] = kwargs.get("source_files", {})

        plan = self.artifacts.find_and_read_task_file(task, "plan.md")
        if not plan:
            return PhaseResult(success=False, message=f"No plan.md for task '{task}'")

        # Determine which stage to implement
        completed = self.artifacts.find_completed_stages(task)
        if stage is None:
            stage = (max(completed) + 1) if completed else 1

        if stage in completed:
            return PhaseResult(
                success=False,
                message=f"Stage {stage} already completed. Use --force to re-run.",
            )

        # Extract only the current stage section from plan
        stage_section = self._extract_stage_section(plan, stage)

        # Get previous stage notes for context continuity
        prev_notes = ""
        if stage > 1:
            prev_dir = self.artifacts.find_stage_dir(task, stage - 1)
            prev_notes_path = prev_dir / "AI_NOTES.md"
            if prev_notes_path.exists():
                prev_notes = prev_notes_path.read_text(encoding="utf-8")

        # Build prompt with stage number injected
        prompt_template = self._load_prompt_template("implement")
        if prompt_template:
            prompt = (
                prompt_template
                .replace("{stage}", str(stage))
                .replace("{stage_section}", stage_section)
            )
        else:
            prompt = (
                f"You MUST implement ONLY Stage {stage} of the plan. Nothing else.\n\n"
                f"Stage {stage} section:\n{stage_section}\n\n"
                "Output ONLY files for this stage. Use FULL relative paths.\n"
                "Format: ```path/to/file.ext\n<content>\n```\n"
                "End with: ```AI_NOTES.md\n<notes>\n```"
            )

        # Build context — order matters for LLM attention
        extra_context: dict[str, str] = {}

        # Architecture — project structure
        architecture = self.artifacts.read_architecture()
        if architecture.strip():
            extra_context["Architecture"] = architecture

        # Spec
        spec = self.artifacts.find_and_read_task_file(task, "spec.md")
        if spec:
            extra_context["Task specification"] = spec

        # Clarifications
        clarifications = self.artifacts.find_and_read_task_file(task, "clarifications.md")
        if clarifications:
            extra_context["Clarifications"] = clarifications

        # Full plan for reference (stage section is already in prompt)
        extra_context["Full plan (for reference)"] = plan

        # Previous stage notes
        if prev_notes:
            extra_context["Previous stage AI_NOTES"] = prev_notes

        # Existing source files — LLM needs to see what's already written
        if not source_files:
            source_files = await self._collect_project_sources_async(max_files=20, max_file_size=10_000)

        if source_files:
            # Bundle existing files so LLM can import from them
            files_text = ""
            for fpath, content in source_files.items():
                files_text += f"\n### {fpath}\n```\n{content}\n```\n"
            extra_context["Current project files (already implemented)"] = files_text

        # Project tree as overview
        project_tree = await self._scan_project_tree_async()
        if project_tree:
            extra_context["Current project file tree"] = project_tree

        messages = self._build_messages(prompt, extra_context)
        response_content = await self._stream_collect(messages, min_tokens=16384, task=task or "")

        # Parse response into files
        files = self._parse_file_blocks(response_content)

        # Extract and save AI_NOTES
        ai_notes = files.pop("AI_NOTES.md", None) or files.pop("ai_notes.md", None)
        if not ai_notes:
            ai_notes = (
                f"# AI_NOTES — Stage {stage}\n\n"
                f"## What was done\n"
                f"Stage {stage} implementation generated.\n\n"
                f"## Files created / modified\n"
                + "\n".join(f"- `{f}`" for f in files.keys())
                + "\n"
            )
        self.artifacts.find_and_create_stage_notes(task, stage, ai_notes)

        # Build file diffs (do NOT write to disk — user reviews first)
        file_diffs: dict[str, dict] = {}
        for fpath, content in files.items():
            target = self.artifacts.root / fpath
            if target.exists():
                try:
                    old_content = target.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    old_content = None
                file_diffs[fpath] = {"old": old_content, "new": content, "is_new": False}
            else:
                file_diffs[fpath] = {"old": None, "new": content, "is_new": True}

        return PhaseResult(
            success=True,
            message=f"Stage {stage} generated: {len(file_diffs)} files ready for review",
            artifacts_created=list(file_diffs.keys()),
            data={
                "stage": stage,
                "files": file_diffs,
                "ai_notes": ai_notes,
            },
        )

    async def stream_run(
        self, task: str | None = None, **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream implementation output."""
        if not task:
            yield "Error: task name is required."
            return

        stage = kwargs.get("stage")
        plan = self.artifacts.find_and_read_task_file(task, "plan.md")
        if not plan:
            yield f"Error: no plan.md for task '{task}'"
            return

        completed = self.artifacts.find_completed_stages(task)
        if stage is None:
            stage = (max(completed) + 1) if completed else 1

        stage_section = self._extract_stage_section(plan, stage)

        prompt = (
            f"You MUST implement ONLY Stage {stage}.\n\n"
            f"Stage section:\n{stage_section}\n\n"
            "Output ONLY created/modified files. Write tests. Create AI_NOTES.md.\n"
            "Do NOT leave stubs. Format: ```path/to/file.ext\n<content>\n```"
        )

        messages = self._build_messages(prompt, {"Plan": plan})
        async for chunk in self.llm.stream(messages):
            yield chunk

    @staticmethod
    def _extract_stage_section(plan: str, stage: int) -> str:
        """Extract a specific stage section from the plan.

        Looks for '## Stage N' headers and returns everything until the next
        stage header or end of document.
        """
        lines = plan.splitlines()
        start = None
        end = None

        # Pattern matches: ## Stage 1, ## Stage 1:, ##Stage 1, etc.
        stage_pattern = re.compile(
            rf"^##\s*(?:Stage|Этап)\s*{stage}\b", re.IGNORECASE
        )
        next_stage_pattern = re.compile(
            r"^##\s*(?:Stage|Этап)\s*\d+", re.IGNORECASE
        )

        for i, line in enumerate(lines):
            if stage_pattern.match(line.strip()):
                start = i
            elif start is not None and next_stage_pattern.match(line.strip()):
                end = i
                break

        if start is not None:
            section = "\n".join(lines[start:end]).strip()
            return section

        # Fallback: return full plan with a note
        return f"(Could not extract Stage {stage} section — full plan below)\n\n{plan}"
