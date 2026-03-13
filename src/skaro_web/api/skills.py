"""Skills management endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from skaro_core.config import load_config, save_config
from skaro_core.skills import list_all_with_status, load_skills_for_phase
from skaro_core.skills.loader import _load_registry, discover_catalog
from skaro_web.api.deps import get_project_root

router = APIRouter(prefix="/api/skills", tags=["skills"])


# ── Schemas ──────────────────────────────────────────────

class SkillsUpdateBody(BaseModel):
    """Update active/disabled skill lists."""
    active: list[str] = Field(default_factory=list)
    disabled: list[str] = Field(default_factory=list)


# ── Endpoints ────────────────────────────────────────────

@router.get("")
async def list_skills(project_root: Path = Depends(get_project_root)):
    """List all available skills with activation status."""
    config = load_config(project_root)
    skills = list_all_with_status(config.skills, project_root)
    return {
        "preset": config.skills.preset,
        "skills": skills,
    }


@router.get("/registry")
async def get_registry():
    """Return the preset → skills mapping from _registry.yaml."""
    return {"presets": _load_registry()}


@router.get("/{skill_name}")
async def get_skill(skill_name: str, project_root: Path = Depends(get_project_root)):
    """Return full details for a specific skill."""
    config = load_config(project_root)
    all_skills = discover_catalog(config.skills, project_root)
    skill = all_skills.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "source": skill.source,
        "phases": skill.phases,
        "roles": skill.roles,
        "instructions": skill.instructions,
        "phase_instructions": skill.phase_instructions,
    }


@router.put("/active")
async def update_active_skills(
    payload: SkillsUpdateBody,
    project_root: Path = Depends(get_project_root),
):
    """Update which skills are active/disabled."""
    config = load_config(project_root)
    config.skills.active = payload.active
    config.skills.disabled = payload.disabled
    save_config(config, project_root)
    return {"success": True}
