"""Skill loader: discovery, loading, merging, and filtering.

Three sources (in priority order, last wins on name conflict):
  1. Preset skills — bundled with the package, linked via _registry.yaml
  2. Global skills — ~/.skaro/skills/*.yaml
  3. User skills  — .skaro/skills/*.yaml (project-level)
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from skaro_core.artifacts._helpers import TEMPLATES_PKG_DIR
from skaro_core.config._models import GLOBAL_CONFIG_DIR, SKARO_DIR, SkillsConfig

from .models import Skill

log = logging.getLogger(__name__)

# ── Directories ──────────────────────────────────────────

_SKILLS_PKG_DIR: Path | None = (
    TEMPLATES_PKG_DIR / "skills" if TEMPLATES_PKG_DIR else None
)

_GLOBAL_SKILLS_DIR = GLOBAL_CONFIG_DIR / "skills"


def _skills_dir_for_project(project_root: Path | None) -> Path | None:
    """Return .skaro/skills/ for a project, or None."""
    if project_root is None:
        return None
    d = project_root / SKARO_DIR / "skills"
    return d if d.is_dir() else None


# ── Registry ─────────────────────────────────────────────

def _load_registry() -> dict[str, list[str]]:
    """Load _registry.yaml mapping preset IDs to skill names."""
    if _SKILLS_PKG_DIR is None:
        return {}
    path = _SKILLS_PKG_DIR / "_registry.yaml"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("presets", {})
    except Exception:
        log.warning("Failed to load skills registry: %s", path, exc_info=True)
        return {}


# ── Single skill loading ────────────────────────────────

def _load_skill_file(path: Path, source: str) -> Skill | None:
    """Load a single .yaml skill file. Returns None on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or not data.get("name"):
            log.warning("Skill file missing 'name': %s", path)
            return None
        return Skill.from_dict(data, source=source)
    except Exception:
        log.warning("Failed to load skill: %s", path, exc_info=True)
        return None


# ── Directory scanning ──────────────────────────────────

def _scan_skills_dir(directory: Path, source: str) -> dict[str, Skill]:
    """Scan a directory for *.yaml skill files. Returns {name: Skill}."""
    skills: dict[str, Skill] = {}
    if not directory.is_dir():
        return skills
    for path in sorted(directory.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        skill = _load_skill_file(path, source=source)
        if skill:
            skills[skill.name] = skill
    return skills


def discover_catalog(
    config_skills: SkillsConfig,
    project_root: Path | None = None,
) -> dict[str, Skill]:
    """Discover ALL available skills from all sources (full catalog).

    Unlike ``discover_all_skills`` which only loads skills for the active
    preset, this function loads every bundled skill file — enabling users
    to browse and activate any skill regardless of preset.

    Returns a merged dict {name: Skill} with user > global > bundled priority.
    """
    skills: dict[str, Skill] = {}

    # 1. ALL bundled skills (scan entire templates/skills/ directory)
    if _SKILLS_PKG_DIR:
        skills.update(_scan_skills_dir(_SKILLS_PKG_DIR, source="bundled"))

    # 2. Global skills (medium priority)
    if _GLOBAL_SKILLS_DIR.is_dir():
        skills.update(_scan_skills_dir(_GLOBAL_SKILLS_DIR, source="global"))

    # 3. User skills (highest priority)
    user_dir = _skills_dir_for_project(project_root)
    if user_dir:
        skills.update(_scan_skills_dir(user_dir, source="user"))

    # Mark preset skills: override source to "preset" for skills that belong
    # to the active preset so the UI can distinguish them.
    if config_skills.preset:
        registry = _load_registry()
        preset_names = set(registry.get(config_skills.preset, []))
        for name in preset_names:
            if name in skills and skills[name].source == "bundled":
                skills[name].source = "preset"

    return skills


def _build_preset_map() -> dict[str, list[str]]:
    """Build reverse map: skill name → list of preset IDs that reference it."""
    registry = _load_registry()
    result: dict[str, list[str]] = {}
    for preset_id, skill_names in registry.items():
        for name in skill_names:
            result.setdefault(name, []).append(preset_id)
    return result


# ── Public API ──────────────────────────────────────────

def discover_all_skills(
    config_skills: SkillsConfig,
    project_root: Path | None = None,
) -> dict[str, Skill]:
    """Discover all available skills from all three sources.

    Returns a merged dict {name: Skill} with user skills overriding
    global, and global overriding preset.
    """
    skills: dict[str, Skill] = {}

    # 1. Preset skills (lowest priority)
    if config_skills.preset and _SKILLS_PKG_DIR:
        registry = _load_registry()
        preset_names = registry.get(config_skills.preset, [])
        for name in preset_names:
            path = _SKILLS_PKG_DIR / f"{name}.yaml"
            if path.exists():
                skill = _load_skill_file(path, source="preset")
                if skill:
                    skills[skill.name] = skill

    # 2. Global skills (medium priority)
    if _GLOBAL_SKILLS_DIR.is_dir():
        skills.update(_scan_skills_dir(_GLOBAL_SKILLS_DIR, source="global"))

    # 3. User skills (highest priority)
    user_dir = _skills_dir_for_project(project_root)
    if user_dir:
        skills.update(_scan_skills_dir(user_dir, source="user"))

    return skills


def load_effective_skills(
    config_skills: SkillsConfig,
    project_root: Path | None = None,
) -> list[Skill]:
    """Load the effective (active) skill set after applying active/disabled filters.

    Effective = (preset skills - disabled) + explicitly active skills from catalog.
    """
    # Use full catalog so explicitly activated non-preset skills are found
    all_skills = discover_catalog(config_skills, project_root)

    disabled = set(config_skills.disabled)
    active_extra = set(config_skills.active)

    result: list[Skill] = []
    for name, skill in all_skills.items():
        if name in disabled:
            continue
        # Preset skills are included by default
        if skill.source == "preset":
            result.append(skill)
        # Non-preset skills require explicit activation
        elif name in active_extra:
            result.append(skill)

    return result


def load_skills_for_phase(
    config_skills: SkillsConfig,
    phase: str,
    role: str | None,
    project_root: Path | None = None,
) -> list[Skill]:
    """Load skills filtered for a specific phase and role."""
    skills = load_effective_skills(config_skills, project_root)
    return [s for s in skills if s.applies_to(phase, role)]


def list_all_with_status(
    config_skills: SkillsConfig,
    project_root: Path | None = None,
) -> list[dict]:
    """List all discoverable skills with their activation status.

    Returns list of dicts with keys: name, description, source, status, presets.
    Status is one of: "active", "disabled", "available".
    Uses the full catalog so users can browse and enable any skill.
    """
    all_skills = discover_catalog(config_skills, project_root)
    disabled = set(config_skills.disabled)
    active_extra = set(config_skills.active)
    effective = {s.name for s in load_effective_skills(config_skills, project_root)}
    preset_map = _build_preset_map()

    result = []
    for name, skill in sorted(all_skills.items()):
        if name in disabled:
            status = "disabled"
        elif name in effective:
            status = "active"
        else:
            status = "available"
        result.append({
            "name": skill.name,
            "description": skill.description,
            "source": skill.source,
            "status": status,
            "phases": skill.phases,
            "roles": skill.roles,
            "presets": preset_map.get(name, []),
        })

    # Also include skills in active list that aren't discovered (missing files)
    known = {s["name"] for s in result}
    for name in active_extra:
        if name not in known:
            result.append({
                "name": name,
                "description": "",
                "source": "unknown",
                "status": "missing",
                "phases": [],
                "roles": [],
                "presets": [],
            })

    return result
