"""Project Review phase: project-wide structural verification and global commands.

Implements Phase 5 (Review / cross-validation) from methodology.md at the
project level.  Runs:
1. Structural checks -- all tasks complete, devplan milestones closed,
   invariants present, constitution validated, all task-level tests confirmed.
2. Global verify commands from config.yaml.

Results are saved to .skaro/docs/review-results.json.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from skaro_core.artifacts import Phase, Status
from skaro_core.phases.base import BasePhase, PhaseResult

_COMMAND_TIMEOUT = 120


class ProjectReviewPhase(BasePhase):
    phase_name = "project_review"

    async def run(self, task: str | None = None, **kwargs: Any) -> PhaseResult:
        checklist = await asyncio.to_thread(self._run_structural_checks)

        global_commands = [
            {"name": vc.name, "command": vc.command}
            for vc in self.config.verify_commands
            if vc.command.strip()
        ]
        global_results = await self._run_commands(global_commands)

        checklist_ok = all(item["passed"] for item in checklist)
        cmds_ok = all(cmd["success"] for cmd in global_results)
        passed = checklist_ok and cmds_ok

        results = {
            "checklist": checklist,
            "global_commands": global_results,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
        }

        docs_dir = self.artifacts.skaro / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        results_path = docs_dir / "review-results.json"
        results_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        total_checks = len(checklist)
        passed_checks = sum(1 for c in checklist if c["passed"])
        summary_parts = [f"Checklist: {passed_checks}/{total_checks}"]

        if global_results:
            ok = sum(1 for c in global_results if c["success"])
            summary_parts.append(f"Global commands: {ok}/{len(global_results)}")

        return PhaseResult(
            success=True,
            message=" | ".join(summary_parts),
            data=results,
        )

    def load_results(self) -> dict[str, Any] | None:
        results_path = self.artifacts.skaro / "docs" / "review-results.json"
        if results_path.exists():
            try:
                return json.loads(results_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def _run_structural_checks(self) -> list[dict]:
        checks: list[dict] = []
        state = self.artifacts.get_project_state()

        checks.append({
            "id": "constitution_validated",
            "label": "Constitution validated",
            "passed": self.artifacts.is_constitution_validated,
            "detail": "Validated" if self.artifacts.is_constitution_validated else "Not validated",
        })

        invariants = self.artifacts.read_invariants()
        has_invariants = bool(invariants and invariants.strip())
        checks.append({
            "id": "invariants_present",
            "label": "Architectural invariants defined",
            "passed": has_invariants,
            "detail": (
                f"{len(invariants.strip().splitlines())} lines"
                if has_invariants else "Empty or missing"
            ),
        })

        checks.append({
            "id": "architecture_reviewed",
            "label": "Architecture reviewed",
            "passed": self.artifacts.is_architecture_reviewed,
            "detail": "Reviewed" if self.artifacts.is_architecture_reviewed else "Not reviewed",
        })

        checks.append({
            "id": "devplan_confirmed",
            "label": "Dev plan confirmed",
            "passed": self.artifacts.is_devplan_confirmed,
            "detail": "Confirmed" if self.artifacts.is_devplan_confirmed else "Not confirmed",
        })

        tasks_total = len(state.tasks)
        tasks_tests_confirmed = sum(
            1 for ts in state.tasks
            if ts.phases.get(Phase.TESTS) == Status.COMPLETE
        )
        all_confirmed = tasks_total > 0 and tasks_tests_confirmed == tasks_total
        checks.append({
            "id": "all_tasks_tests_confirmed",
            "label": "All task tests confirmed",
            "passed": all_confirmed,
            "detail": f"{tasks_tests_confirmed}/{tasks_total} tasks",
        })

        tasks_impl_done = sum(
            1 for ts in state.tasks
            if ts.phases.get(Phase.IMPLEMENT) == Status.COMPLETE
        )
        all_impl = tasks_total > 0 and tasks_impl_done == tasks_total
        checks.append({
            "id": "all_tasks_implemented",
            "label": "All tasks fully implemented",
            "passed": all_impl,
            "detail": f"{tasks_impl_done}/{tasks_total} tasks",
        })

        milestones = self.artifacts.list_milestones()
        milestone_tasks: dict[str, int] = {}
        for ts in state.tasks:
            milestone_tasks[ts.milestone] = milestone_tasks.get(ts.milestone, 0) + 1
        empty_milestones = [m for m in milestones if milestone_tasks.get(m, 0) == 0]
        checks.append({
            "id": "milestones_have_tasks",
            "label": "All milestones have tasks",
            "passed": len(empty_milestones) == 0 and len(milestones) > 0,
            "detail": (
                f"{len(milestones)} milestone(s), all with tasks"
                if not empty_milestones
                else f"Empty: {', '.join(empty_milestones[:5])}"
            ),
        })

        return checks

    async def _run_commands(self, commands: list[dict[str, str]]) -> list[dict]:
        results: list[dict] = []
        for cmd_def in commands:
            if not cmd_def.get("command", "").strip():
                continue
            result = await self._execute_command(cmd_def["name"], cmd_def["command"])
            results.append(result)
        return results

    async def _execute_command(self, name: str, command: str) -> dict:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.artifacts.root),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=_COMMAND_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "name": name, "command": command, "success": False,
                    "exit_code": -1, "stdout": "",
                    "stderr": f"Command timed out after {_COMMAND_TIMEOUT}s",
                }

            return {
                "name": name,
                "command": command,
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace")[-5000:],
                "stderr": stderr.decode("utf-8", errors="replace")[-5000:],
            }
        except Exception as exc:
            return {
                "name": name, "command": command, "success": False,
                "exit_code": -1, "stdout": "", "stderr": str(exc),
            }
