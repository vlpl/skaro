"""Tests for the skaro_core.skills module."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skaro_core.skills.models import Skill
from skaro_core.config._models import SkillsConfig
from skaro_core.skills.loader import (
    _load_skill_file,
    _scan_skills_dir,
    discover_all_skills,
    list_all_with_status,
    load_effective_skills,
    load_skills_for_phase,
)


# ── Skill model tests ───────────────────────────────────


class TestSkillModel:
    def test_from_dict_minimal(self):
        skill = Skill.from_dict({"name": "test"}, source="user")
        assert skill.name == "test"
        assert skill.source == "user"
        assert skill.instructions == ""
        assert skill.phases == []
        assert skill.roles == []

    def test_from_dict_full(self):
        data = {
            "name": "react-components",
            "description": "React best practices",
            "version": "1.0",
            "phases": ["implement", "plan"],
            "roles": ["coder"],
            "instructions": "Use functional components",
            "phase_instructions": {
                "plan": "Plan component hierarchy",
            },
        }
        skill = Skill.from_dict(data, source="preset")
        assert skill.name == "react-components"
        assert skill.description == "React best practices"
        assert skill.phases == ["implement", "plan"]
        assert skill.roles == ["coder"]
        assert skill.source == "preset"
        assert skill.phase_instructions["plan"] == "Plan component hierarchy"

    def test_applies_to_no_filters(self):
        skill = Skill(name="test")
        assert skill.applies_to("implement", "coder") is True
        assert skill.applies_to("plan", None) is True

    def test_applies_to_phase_filter(self):
        skill = Skill(name="test", phases=["implement", "tests"])
        assert skill.applies_to("implement", "coder") is True
        assert skill.applies_to("plan", "coder") is False

    def test_applies_to_role_filter(self):
        skill = Skill(name="test", roles=["coder"])
        assert skill.applies_to("implement", "coder") is True
        assert skill.applies_to("implement", "reviewer") is False
        assert skill.applies_to("implement", None) is True  # no role = no filter

    def test_applies_to_both_filters(self):
        skill = Skill(name="test", phases=["implement"], roles=["coder"])
        assert skill.applies_to("implement", "coder") is True
        assert skill.applies_to("plan", "coder") is False
        assert skill.applies_to("implement", "reviewer") is False

    def test_get_instructions_general(self):
        skill = Skill(name="test", instructions="General instructions")
        assert skill.get_instructions("implement") == "General instructions"

    def test_get_instructions_phase_override(self):
        skill = Skill(
            name="test",
            instructions="General",
            phase_instructions={"plan": "Plan-specific"},
        )
        assert skill.get_instructions("plan") == "Plan-specific"
        assert skill.get_instructions("implement") == "General"

    def test_get_instructions_empty_phase_falls_back(self):
        skill = Skill(
            name="test",
            instructions="General",
            phase_instructions={"plan": ""},
        )
        # Empty phase instruction falls back to general
        assert skill.get_instructions("plan") == "General"


# ── SkillsConfig tests ──────────────────────────────────


class TestSkillsConfig:
    def test_default(self):
        sc = SkillsConfig()
        assert sc.preset == ""
        assert sc.active == []
        assert sc.disabled == []

    def test_from_dict(self):
        sc = SkillsConfig.from_dict({
            "preset": "react",
            "active": ["custom-skill"],
            "disabled": ["react-testing"],
        })
        assert sc.preset == "react"
        assert sc.active == ["custom-skill"]
        assert sc.disabled == ["react-testing"]

    def test_from_dict_empty(self):
        sc = SkillsConfig.from_dict({})
        assert sc.preset == ""
        assert sc.active == []

    def test_to_dict_empty(self):
        sc = SkillsConfig()
        assert sc.to_dict() == {}

    def test_to_dict_with_values(self):
        sc = SkillsConfig(preset="react", active=["custom"], disabled=["ts"])
        d = sc.to_dict()
        assert d["preset"] == "react"
        assert d["active"] == ["custom"]
        assert d["disabled"] == ["ts"]

    def test_roundtrip(self):
        original = SkillsConfig(preset="fastapi", active=["a", "b"], disabled=["c"])
        restored = SkillsConfig.from_dict(original.to_dict())
        assert restored.preset == original.preset
        assert restored.active == original.active
        assert restored.disabled == original.disabled


# ── Loader tests ────────────────────────────────────────


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with test skills."""
    d = tmp_path / "skills"
    d.mkdir()

    (d / "skill-a.yaml").write_text(yaml.dump({
        "name": "skill-a",
        "description": "Skill A",
        "phases": ["implement"],
        "instructions": "Do A things",
    }), encoding="utf-8")

    (d / "skill-b.yaml").write_text(yaml.dump({
        "name": "skill-b",
        "description": "Skill B",
        "roles": ["coder"],
        "instructions": "Do B things",
    }), encoding="utf-8")

    # Invalid skill (no name)
    (d / "bad.yaml").write_text(yaml.dump({
        "description": "No name",
    }), encoding="utf-8")

    # Underscore-prefixed (should be skipped)
    (d / "_internal.yaml").write_text(yaml.dump({
        "name": "internal",
    }), encoding="utf-8")

    return d


class TestLoader:
    def test_load_skill_file(self, skills_dir: Path):
        skill = _load_skill_file(skills_dir / "skill-a.yaml", source="user")
        assert skill is not None
        assert skill.name == "skill-a"
        assert skill.source == "user"
        assert skill.instructions == "Do A things"

    def test_load_skill_file_invalid(self, skills_dir: Path):
        skill = _load_skill_file(skills_dir / "bad.yaml", source="user")
        assert skill is None

    def test_load_skill_file_missing(self, skills_dir: Path):
        skill = _load_skill_file(skills_dir / "nonexistent.yaml", source="user")
        assert skill is None

    def test_scan_skills_dir(self, skills_dir: Path):
        skills = _scan_skills_dir(skills_dir, source="user")
        assert "skill-a" in skills
        assert "skill-b" in skills
        # bad.yaml should be excluded (no name)
        assert "bad" not in skills
        # _internal.yaml should be excluded (starts with _)
        assert "internal" not in skills

    def test_scan_skills_dir_nonexistent(self, tmp_path: Path):
        skills = _scan_skills_dir(tmp_path / "nope", source="user")
        assert skills == {}


# ── Integration tests with project structure ────────────


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal Skaro project structure with skills."""
    skaro = tmp_path / ".skaro"
    skaro.mkdir()
    skills = skaro / "skills"
    skills.mkdir()

    # User skill
    (skills / "my-custom.yaml").write_text(yaml.dump({
        "name": "my-custom",
        "description": "Custom skill",
        "instructions": "Custom instructions",
    }), encoding="utf-8")

    return tmp_path


class TestEffectiveSkills:
    def test_no_skills_configured(self, project: Path):
        config = SkillsConfig()
        result = load_effective_skills(config, project)
        # my-custom exists but is not in active list
        assert len(result) == 0

    def test_active_user_skill(self, project: Path):
        config = SkillsConfig(active=["my-custom"])
        result = load_effective_skills(config, project)
        assert len(result) == 1
        assert result[0].name == "my-custom"

    def test_disabled_skill(self, project: Path):
        config = SkillsConfig(active=["my-custom"], disabled=["my-custom"])
        result = load_effective_skills(config, project)
        assert len(result) == 0

    def test_phase_filtering(self, project: Path):
        # Add a phase-restricted skill
        skill_path = project / ".skaro" / "skills" / "plan-only.yaml"
        skill_path.write_text(yaml.dump({
            "name": "plan-only",
            "phases": ["plan"],
            "instructions": "Only for plan",
        }), encoding="utf-8")

        config = SkillsConfig(active=["plan-only"])
        plan_skills = load_skills_for_phase(config, "plan", "coder", project)
        impl_skills = load_skills_for_phase(config, "implement", "coder", project)

        assert len(plan_skills) == 1
        assert plan_skills[0].name == "plan-only"
        assert len(impl_skills) == 0

    def test_role_filtering(self, project: Path):
        skill_path = project / ".skaro" / "skills" / "coder-only.yaml"
        skill_path.write_text(yaml.dump({
            "name": "coder-only",
            "roles": ["coder"],
            "instructions": "Only for coder",
        }), encoding="utf-8")

        config = SkillsConfig(active=["coder-only"])
        coder_skills = load_skills_for_phase(config, "implement", "coder", project)
        reviewer_skills = load_skills_for_phase(config, "implement", "reviewer", project)

        assert len(coder_skills) == 1
        assert len(reviewer_skills) == 0


class TestListAllWithStatus:
    def test_list_with_active(self, project: Path):
        config = SkillsConfig(active=["my-custom"])
        items = list_all_with_status(config, project)

        by_name = {i["name"]: i for i in items}
        assert "my-custom" in by_name
        assert by_name["my-custom"]["status"] == "active"
        assert by_name["my-custom"]["source"] == "user"

    def test_list_with_disabled(self, project: Path):
        config = SkillsConfig(active=["my-custom"], disabled=["my-custom"])
        items = list_all_with_status(config, project)

        by_name = {i["name"]: i for i in items}
        assert by_name["my-custom"]["status"] == "disabled"

    def test_list_available_not_active(self, project: Path):
        config = SkillsConfig()
        items = list_all_with_status(config, project)

        by_name = {i["name"]: i for i in items}
        assert by_name["my-custom"]["status"] == "available"

    def test_missing_skill_in_active(self, project: Path):
        config = SkillsConfig(active=["nonexistent-skill"])
        items = list_all_with_status(config, project)

        by_name = {i["name"]: i for i in items}
        assert "nonexistent-skill" in by_name
        assert by_name["nonexistent-skill"]["status"] == "missing"

    def test_catalog_shows_all_bundled(self, project: Path):
        """Full catalog is visible even without a preset."""
        config = SkillsConfig()
        items = list_all_with_status(config, project)

        by_name = {i["name"]: i for i in items}
        # Bundled skills should be visible as 'available'
        assert "react-components" in by_name
        assert "fastapi-endpoints" in by_name
        assert by_name["react-components"]["status"] == "available"

    def test_catalog_shows_presets_field(self, project: Path):
        """Each skill shows which presets reference it."""
        config = SkillsConfig()
        items = list_all_with_status(config, project)

        by_name = {i["name"]: i for i in items}
        ts = by_name.get("typescript-strict")
        assert ts is not None
        assert "react" in ts["presets"]
        assert len(ts["presets"]) >= 7

    def test_enable_bundled_skill_without_preset(self, project: Path):
        """User can activate any bundled skill without setting a preset."""
        config = SkillsConfig(active=["django-patterns"])
        effective = load_effective_skills(config, project)
        names = [s.name for s in effective]
        assert "django-patterns" in names


# ── SkaroConfig integration ─────────────────────────────


class TestSkaroConfigSkills:
    def test_config_roundtrip(self):
        from skaro_core.config import SkaroConfig

        config = SkaroConfig()
        config.skills = SkillsConfig(preset="react", active=["custom"], disabled=["ts"])

        d = config.to_dict()
        assert d["skills"]["preset"] == "react"
        assert d["skills"]["active"] == ["custom"]

        restored = SkaroConfig.from_dict(d)
        assert restored.skills.preset == "react"
        assert restored.skills.active == ["custom"]
        assert restored.skills.disabled == ["ts"]

    def test_config_no_skills_section(self):
        from skaro_core.config import SkaroConfig

        config = SkaroConfig.from_dict({"llm": {"provider": "anthropic"}})
        assert config.skills.preset == ""
        assert config.skills.active == []

    def test_config_empty_skills(self):
        from skaro_core.config import SkaroConfig

        config = SkaroConfig()
        d = config.to_dict()
        # Empty skills should not appear in serialized output
        assert "skills" not in d
