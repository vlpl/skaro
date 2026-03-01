"""Status, dashboard, statistics, and diagnostics endpoints."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from skaro_core.artifacts import ArtifactManager
from skaro_core.config import load_config, load_token_usage, load_usage_log
from skaro_core.phases.base import SKIP_DIRS
from skaro_web.api.deps import get_am, get_project_root

router = APIRouter(prefix="/api", tags=["status"])

STATIC_DIR = Path(__file__).parent.parent / "static"
DASHBOARD_FILE = Path(__file__).parent.parent / "dashboard.html"


def _build_status(am: ArtifactManager, project_root: Path) -> dict[str, Any]:
    """Build project status dict (reused by /status and /dashboard)."""
    if not am.is_initialized:
        return {"initialized": False}

    state = am.get_project_state()
    tasks = [
        {
            "name": ts.name,
            "milestone": ts.milestone,
            "current_phase": ts.current_phase.value,
            "current_stage": ts.current_stage,
            "total_stages": ts.total_stages,
            "progress_percent": ts.progress_percent,
            "phases": {p.value: s.value for p, s in ts.phases.items()},
        }
        for ts in state.tasks
    ]

    config = load_config(project_root)
    tokens = load_token_usage(project_root)

    roles_info: dict[str, Any] = {}
    for rname, rc in config.roles.items():
        if rc.is_active:
            roles_info[rname] = {"provider": rc.provider, "model": rc.model}
        else:
            roles_info[rname] = None

    return {
        "initialized": True,
        "project_name": config.project_name,
        "project_description": config.project_description,
        "has_constitution": state.has_constitution,
        "constitution_validated": am.is_constitution_validated,
        "has_invariants": bool(am.read_invariants().strip()),
        "has_architecture": am.has_architecture,
        "architecture_reviewed": am.is_architecture_reviewed,
        "has_devplan": am.has_devplan,
        "devplan_confirmed": am.is_devplan_confirmed,
        "adr_count": len(am.list_adrs()),
        "tasks": tasks,
        "config": {
            "llm_provider": config.llm.provider,
            "llm_model": config.llm.model,
            "lang": config.lang,
            "roles": roles_info,
        },
        "tokens": tokens,
    }


def _build_stats(project_root: Path) -> dict[str, Any]:
    """Build usage statistics + project file counts."""
    tokens = load_token_usage(project_root)
    log = load_usage_log(project_root)

    by_phase: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0})
    by_task: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0})
    by_model: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0})
    by_role: dict[str, dict] = defaultdict(lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0})

    for e in log:
        inp = e.get("input_tokens", 0)
        out = e.get("output_tokens", 0)

        phase = e.get("phase", "unknown")
        by_phase[phase]["requests"] += 1
        by_phase[phase]["input_tokens"] += inp
        by_phase[phase]["output_tokens"] += out

        task_name = e.get("feature") or e.get("task") or "(global)"
        by_task[task_name]["requests"] += 1
        by_task[task_name]["input_tokens"] += inp
        by_task[task_name]["output_tokens"] += out

        model = e.get("model", "unknown")
        by_model[model]["requests"] += 1
        by_model[model]["input_tokens"] += inp
        by_model[model]["output_tokens"] += out

        role = e.get("role") or "default"
        by_role[role]["requests"] += 1
        by_role[role]["input_tokens"] += inp
        by_role[role]["output_tokens"] += out

    file_counts: dict[str, int] = defaultdict(int)
    total_lines = 0

    if project_root and project_root.is_dir():
        for path in project_root.rglob("*"):
            parts = path.relative_to(project_root).parts
            if any(p in SKIP_DIRS or p.startswith(".") for p in parts):
                continue
            if path.is_file() and path.suffix:
                ext = path.suffix.lower()
                file_counts[ext] += 1
                if ext in {
                    ".py", ".js", ".ts", ".jsx", ".tsx", ".svelte", ".vue",
                    ".go", ".rs", ".java", ".rb", ".css", ".html", ".md",
                }:
                    try:
                        total_lines += sum(1 for _ in open(path, encoding="utf-8", errors="ignore"))
                    except (PermissionError, OSError):
                        pass

    return {
        "tokens": tokens,
        "total_requests": len(log),
        "by_phase": dict(by_phase),
        "by_task": dict(by_task),
        "by_model": dict(by_model),
        "by_role": dict(by_role),
        "files": dict(sorted(file_counts.items(), key=lambda x: -x[1])),
        "total_files": sum(file_counts.values()),
        "total_lines": total_lines,
        "log_entries": log[-50:][::-1],
    }


# ── Endpoints ───────────────────────────────────

@router.get("/status")
async def get_status(
    am: ArtifactManager = Depends(get_am),
    project_root: Path = Depends(get_project_root),
):
    return _build_status(am, project_root)


@router.get("/tokens")
async def get_tokens(project_root: Path = Depends(get_project_root)):
    return load_token_usage(project_root)


@router.get("/stats")
async def get_stats(project_root: Path = Depends(get_project_root)):
    """Full usage statistics + project file counts."""
    return await asyncio.to_thread(_build_stats, project_root)


@router.get("/dashboard")
async def get_dashboard(
    am: ArtifactManager = Depends(get_am),
    project_root: Path = Depends(get_project_root),
):
    """Combined dashboard data: project status + usage statistics in one request."""
    return {
        "status": _build_status(am, project_root),
        "stats": await asyncio.to_thread(_build_stats, project_root),
    }


@router.get("/debug/static")
async def debug_static():
    """Debug endpoint: shows what files the server can find."""
    info = {
        "STATIC_DIR": str(STATIC_DIR),
        "STATIC_DIR_exists": STATIC_DIR.is_dir(),
        "DASHBOARD_FILE": str(DASHBOARD_FILE),
        "DASHBOARD_FILE_exists": DASHBOARD_FILE.exists(),
        "index_html_exists": (STATIC_DIR / "index.html").is_file(),
        "_app_dir_exists": (STATIC_DIR / "_app").is_dir(),
    }
    if STATIC_DIR.is_dir():
        info["static_contents"] = sorted(
            str(p.relative_to(STATIC_DIR))
            for p in STATIC_DIR.rglob("*")
            if p.is_file()
        )[:30]
    return info
