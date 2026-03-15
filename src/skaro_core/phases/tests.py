"""Tests phase: structural verification and command execution.

Replaces the old Review phase with concrete, actionable checks:
1. Structural checklist — files from plan exist, test files present.
2. Command execution — task-level commands from verify.yaml + global from config.yaml.

Results are saved to tests.json inside the task directory.
User confirms completion via a separate endpoint.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from skaro_core.phases._command_runner import CommandRunnerMixin
from skaro_core.phases._plan_utils import count_plan_stages
from skaro_core.phases.base import BasePhase, PhaseResult, SKIP_DIRS

# Patterns for detecting test files
_TEST_FILE_PATTERNS = [
    re.compile(r"test[_\-].*\.(py|js|ts|jsx|tsx)$", re.IGNORECASE),
    re.compile(r".*[_\-]test\.(py|js|ts|jsx|tsx)$", re.IGNORECASE),
    re.compile(r".*\.test\.(js|ts|jsx|tsx)$", re.IGNORECASE),
    re.compile(r".*\.spec\.(js|ts|jsx|tsx)$", re.IGNORECASE),
]

class TestsPhase(CommandRunnerMixin, BasePhase):
    phase_name = "tests"

    async def run(self, task: str | None = None, **kwargs: Any) -> PhaseResult:
        if not task:
            return PhaseResult(success=False, message="Task name is required.")

        plan = self.artifacts.find_and_read_task_file(task, "plan.md")
        if not plan:
            return PhaseResult(success=False, message=f"No plan.md for task '{task}'")

        # ── 1. Structural checklist ─────────────────
        checklist = await asyncio.to_thread(self._run_structural_checks, task, plan)

        # ── 2. Collect task-specific commands ────────
        task_commands = self._load_task_commands(task)

        # ── 3. Run task commands ────────────────────
        task_results = await self._run_commands(task_commands)

        # ── 4. Determine overall result ─────────────
        checklist_ok = all(item["passed"] for item in checklist)
        task_cmds_ok = all(cmd["success"] for cmd in task_results)
        passed = checklist_ok and task_cmds_ok

        results = {
            "checklist": checklist,
            "task_commands": task_results,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
        }

        # ── 5. Save results ─────────────────────────
        self.artifacts.find_and_write_task_file(
            task, "tests.json", json.dumps(results, ensure_ascii=False, indent=2)
        )

        # Remove confirmed marker if re-running tests
        task_dir = self.artifacts.find_task_dir(task)
        confirmed_path = task_dir / "tests-confirmed"
        if confirmed_path.exists():
            confirmed_path.unlink()

        summary_parts = []
        total_checks = len(checklist)
        passed_checks = sum(1 for c in checklist if c["passed"])
        summary_parts.append(f"Checklist: {passed_checks}/{total_checks}")

        if task_results:
            ok = sum(1 for c in task_results if c["success"])
            summary_parts.append(f"Task commands: {ok}/{len(task_results)}")

        return PhaseResult(
            success=True,
            message=" | ".join(summary_parts),
            data=results,
        )

    def confirm(self, task: str) -> PhaseResult:
        """Mark tests as confirmed by the user."""
        task_dir = self.artifacts.find_task_dir(task)
        confirmed_path = task_dir / "tests-confirmed"
        confirmed_path.parent.mkdir(parents=True, exist_ok=True)
        confirmed_path.write_text(
            datetime.now().isoformat(), encoding="utf-8"
        )
        return PhaseResult(success=True, message="Tests confirmed.")

    # ── Verify commands I/O ─────────────────────────

    def _load_task_commands(self, task: str) -> list[dict[str, str]]:
        """Load task-specific verify commands from verify.yaml."""
        task_dir = self.artifacts.find_task_dir(task)
        return self.load_task_commands_static(task_dir)

    @staticmethod
    def load_task_commands_static(task_dir: Path) -> list[dict[str, str]]:
        """Load task verify commands (for API use without full phase init)."""
        verify_path = task_dir / "verify.yaml"
        if not verify_path.exists():
            return []
        try:
            data = yaml.safe_load(verify_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [
                    {"name": str(c.get("name", "")), "command": str(c.get("command", ""))}
                    for c in data
                    if isinstance(c, dict) and c.get("command", "").strip()
                ]
        except (yaml.YAMLError, OSError):
            pass
        return []

    @staticmethod
    def save_task_commands(task_dir: Path, commands: list[dict[str, str]]) -> None:
        """Save task verify commands to verify.yaml."""
        verify_path = task_dir / "verify.yaml"
        verify_path.parent.mkdir(parents=True, exist_ok=True)
        verify_path.write_text(
            yaml.dump(commands, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

    # ── Issues extraction ─────────────────────────────

    @staticmethod
    def extract_issues(results: dict) -> list[dict]:
        """Extract structured issues from tests results.

        Returns a list of dicts, each with:
            id, type ('check' | 'command'), severity ('error' | 'warning'),
            title, detail, command (optional), output (optional).
        """
        issues: list[dict] = []
        idx = 0

        for check in results.get("checklist", []):
            if not check.get("passed"):
                idx += 1
                issues.append({
                    "id": f"chk-{idx}",
                    "type": "check",
                    "severity": "warning",
                    "title": check.get("label", f"Check {idx}"),
                    "detail": check.get("detail", ""),
                })

        for cmd in results.get("task_commands", []):
            if not cmd.get("success"):
                idx += 1
                output = (cmd.get("stderr") or cmd.get("stdout") or "").strip()
                if len(output) > 3000:
                    output = output[-3000:]
                issues.append({
                    "id": f"cmd-{idx}",
                    "type": "command",
                    "severity": "error",
                    "title": cmd.get("name", f"Command {idx}"),
                    "detail": f"Exit code {cmd.get('exit_code', '?')}",
                    "command": cmd.get("command", ""),
                    "output": output,
                })

        return issues

    @staticmethod
    def build_fix_prompt(
        issues: list[dict],
        *,
        verify_commands: list[dict[str, str]] | None = None,
        environment_hint: str = "",
    ) -> str:
        """Build a structured fix prompt from selected issues.

        The prompt gives LLM:
        - HOW tests were run (verify commands)
        - WHERE they were run (environment)
        - WHAT failed (issues with full output)
        - Clear guidance on diagnosis vs blind code changes.
        """
        parts: list[str] = []

        # ── Environment & commands context ──
        if verify_commands or environment_hint:
            parts.append("## Test execution context\n")
            if environment_hint:
                parts.append(f"**Environment**: {environment_hint}\n")
            if verify_commands:
                parts.append("**Verify commands** (from verify.yaml):")
                for vc in verify_commands:
                    name = vc.get("name", "")
                    cmd = vc.get("command", "")
                    parts.append(f"- `{cmd}`" + (f"  ({name})" if name else ""))
                parts.append("")

        # ── Issues ──
        parts.append("## Issues found during automated testing\n")

        for i, issue in enumerate(issues, 1):
            parts.append(f"### Issue {i}: {issue['title']}")
            parts.append(f"- **Type**: {issue['type']}")
            parts.append(f"- **Severity**: {issue['severity']}")
            if issue.get("detail"):
                parts.append(f"- **Detail**: {issue['detail']}")
            if issue.get("command"):
                parts.append(f"- **Command**: `{issue['command']}`")
            if issue.get("output"):
                parts.append(f"- **Output**:\n```\n{issue['output']}\n```")
            parts.append("")

        # ── Guidance ──
        parts.append("## Instructions\n")
        parts.append(
            "CRITICAL: Diagnose the ROOT CAUSE before doing anything else.\n\n"
            "Common root causes that do NOT require code changes:\n"
            "- Wrong execution environment (commands run on host but project runs in Docker)\n"
            "- Python/Node/etc not on PATH, virtual environment not activated\n"
            "- Incorrect paths in verify commands (cd to wrong directory)\n"
            "- Missing dependencies not installed\n"
            "- Test configuration issues (wrong working directory, missing env vars)\n\n"
            "If ANY of the above is the root cause:\n"
            "→ Do NOT output any source code files\n"
            "→ Do NOT rewrite, refactor, or 'improve' existing code\n"
            "→ Explain the root cause and suggest how to fix the verify commands "
            "or environment\n\n"
            "Only output source code files if the root cause is a genuine bug "
            "in the source code itself."
        )
        return "\n".join(parts)

    @staticmethod
    def extract_file_paths(issues: list[dict], project_root: Path) -> list[str]:
        """Extract project file paths mentioned in issue outputs.

        Scans tracebacks and error messages for file references that
        exist in the project tree. Used for auto-scope in fix-from-issues.

        Returns de-duplicated list of relative paths.
        """
        import os

        text = ""
        for issue in issues:
            if issue.get("output"):
                text += issue["output"] + "\n"
            if issue.get("command"):
                text += issue["command"] + "\n"
            if issue.get("detail"):
                text += issue["detail"] + "\n"

        if not text:
            return []

        # Patterns that capture file paths:
        candidates: set[str] = set()

        # Python traceback: File "path"
        for m in re.finditer(r'File "([^"]+)"', text):
            candidates.add(m.group(1))

        # path:line or path:line:col
        for m in re.finditer(r'(\S+\.\w{1,5}):\d+', text):
            candidates.add(m.group(1))

        # Pytest FAILED marker
        for m in re.finditer(r'FAILED\s+(\S+?)::', text):
            candidates.add(m.group(1))

        # Resolve to existing project files
        found: list[str] = []
        seen: set[str] = set()

        for candidate in candidates:
            # Normalize
            candidate = candidate.replace("\\", "/")
            # Strip leading ./ or /
            candidate = candidate.lstrip("./")

            # Try as-is relative to project root
            full = project_root / candidate
            if full.is_file():
                rel = str(full.relative_to(project_root)).replace(os.sep, "/")
                if rel not in seen:
                    seen.add(rel)
                    found.append(rel)
                continue

            # Try without common prefixes (e.g. /app/src/... → src/...)
            parts = candidate.split("/")
            for start in range(1, min(len(parts), 4)):
                sub = "/".join(parts[start:])
                full = project_root / sub
                if full.is_file():
                    rel = str(full.relative_to(project_root)).replace(os.sep, "/")
                    if rel not in seen:
                        seen.add(rel)
                        found.append(rel)
                    break

        return sorted(found)

    # ── Structural checks ───────────────────────────

    def _run_structural_checks(self, task: str, plan: str) -> list[dict]:
        """Run structural verification against the plan."""
        checks: list[dict] = []
        root = self.artifacts.root

        # Scan existing project files (used by test files check)
        existing_files = set()
        for path in root.rglob("*"):
            parts = path.relative_to(root).parts
            # Skip dot-directories (.git, .venv) but NOT dot-files (.env, .eslintrc)
            if any(p in SKIP_DIRS or p.startswith(".") for p in parts[:-1]):
                continue
            if path.is_file():
                existing_files.add(str(path.relative_to(root)).replace("\\", "/"))

        # Check 1: test files exist in the project
        test_files: list[str] = []
        for fpath in existing_files:
            filename = fpath.split("/")[-1]
            if any(p.match(filename) for p in _TEST_FILE_PATTERNS):
                test_files.append(fpath)

        checks.append({
            "id": "test_files_exist",
            "label": "Test files present",
            "passed": len(test_files) > 0,
            "detail": (
                f"{len(test_files)} test file(s) found"
                if test_files
                else "No test files found"
            ),
        })

        # Check 2: spec.md exists and is non-empty
        spec = self.artifacts.find_and_read_task_file(task, "spec.md")
        spec_filled = bool(spec and len(spec.strip()) > 50)
        checks.append({
            "id": "spec_exists",
            "label": "Specification filled",
            "passed": spec_filled,
            "detail": f"{len(spec)} chars" if spec else "Missing",
        })

        # Check 3: all stages completed
        completed = self.artifacts.find_completed_stages(task)
        plan_stages = count_plan_stages(plan)
        all_stages_done = plan_stages > 0 and len(completed) >= plan_stages
        checks.append({
            "id": "stages_complete",
            "label": "All stages implemented",
            "passed": all_stages_done,
            "detail": f"{len(completed)}/{plan_stages} stages",
        })

        return checks
