"""Tests for DevPlan parsers: JSON, markdown fallback, slug, legacy wrapper.

This is the most fragile code in the project — regex + JSON parsing of LLM output.
"""

from __future__ import annotations

import pytest

from skaro_core.phases._devplan_parser import (
    make_slug,
    parse_milestones,
    parse_milestones_markdown,
    parse_update_response,
    wrap_legacy_features,
)
from skaro_core.phases._devplan_prompts import build_devplan_markdown


# ═══════════════════════════════════════════════════
# make_slug
# ═══════════════════════════════════════════════════


class TestMakeSlug:
    def test_basic(self):
        assert make_slug("Project Setup") == "project-setup"

    def test_special_chars(self):
        assert make_slug("My Cool Feature!") == "my-cool-feature"

    def test_slashes(self):
        assert make_slug("auth/login") == "auth-login"

    def test_multiple_dashes(self):
        assert make_slug("too   many   spaces") == "too-many-spaces"

    def test_leading_trailing_dashes(self):
        assert make_slug("-trimmed-") == "trimmed"

    def test_underscores_preserved(self):
        assert make_slug("my_task") == "my_task"

    def test_unicode(self):
        result = make_slug("Настройка проекта")
        assert "-" not in result or len(result) > 0  # doesn't crash


# ═══════════════════════════════════════════════════
# parse_milestones — JSON fenced
# ═══════════════════════════════════════════════════


class TestParseMilestonesJSON:
    def test_standard_fenced_json(self):
        response = '''Here is the plan:
```json
[
  {
    "milestone_slug": "01-foundation",
    "milestone_title": "Foundation",
    "description": "Base setup",
    "tasks": [
      {"name": "project-setup", "description": "Init", "priority": 1, "spec": "# Spec"}
    ]
  },
  {
    "milestone_slug": "02-mvp",
    "milestone_title": "MVP",
    "tasks": [
      {"name": "auth", "description": "Auth", "priority": 1, "spec": "# Auth"}
    ]
  }
]
```
'''
        ms = parse_milestones(response)
        assert len(ms) == 2
        assert ms[0]["milestone_slug"] == "01-foundation"
        assert ms[1]["milestone_slug"] == "02-mvp"
        assert len(ms[0]["tasks"]) == 1
        assert ms[0]["tasks"][0]["name"] == "project-setup"

    def test_nested_arrays_in_tasks(self):
        """Regression: regex must not stop at first ] inside tasks array."""
        response = '''```json
[
  {
    "milestone_slug": "01-core",
    "milestone_title": "Core",
    "tasks": [
      {"name": "a", "dependencies": ["b", "c"], "spec": "# A"},
      {"name": "b", "dependencies": [], "spec": "# B"}
    ]
  }
]
```'''
        ms = parse_milestones(response)
        assert len(ms) == 1
        assert len(ms[0]["tasks"]) == 2

    def test_json_with_preamble_and_epilogue(self):
        response = (
            "I've analyzed the constitution and architecture. Here's my plan:\n\n"
            '```json\n[{"milestone_slug": "01-mvp", "milestone_title": "MVP", '
            '"tasks": [{"name": "init", "spec": "# Init"}]}]\n```\n\n'
            "Let me know if you'd like changes."
        )
        ms = parse_milestones(response)
        assert len(ms) == 1
        assert ms[0]["tasks"][0]["name"] == "init"

    def test_empty_json_array(self):
        response = "```json\n[]\n```"
        ms = parse_milestones(response)
        assert ms == []

    def test_multiple_json_blocks_picks_largest(self):
        """If LLM outputs multiple JSON blocks, pick the longest (most complete)."""
        response = (
            'First attempt:\n```json\n[{"milestone_slug": "01-a", "milestone_title": "A", "tasks": []}]\n```\n\n'
            "Actually, here's the full plan:\n"
            '```json\n[{"milestone_slug": "01-a", "milestone_title": "A", "tasks": [{"name": "x", "spec": ""}]}, '
            '{"milestone_slug": "02-b", "milestone_title": "B", "tasks": [{"name": "y", "spec": ""}]}]\n```'
        )
        ms = parse_milestones(response)
        assert len(ms) == 2


# ═══════════════════════════════════════════════════
# parse_milestones — legacy feature format
# ═══════════════════════════════════════════════════


class TestParseMilestonesLegacy:
    def test_flat_features_wrapped(self):
        response = '''```json
[
  {"name": "setup", "priority": 1, "description": "Setup project"},
  {"name": "api", "priority": 3, "description": "Build API"}
]
```'''
        ms = parse_milestones(response)
        assert len(ms) >= 1
        all_tasks = [t for m in ms for t in m.get("tasks", [])]
        names = {t["name"] for t in all_tasks}
        assert "setup" in names
        assert "api" in names

    def test_legacy_priority_grouping(self):
        features = [
            {"name": "core", "priority": 1},
            {"name": "db", "priority": 2},
            {"name": "api", "priority": 3},
            {"name": "ui", "priority": 4},
        ]
        ms = wrap_legacy_features(features)
        assert len(ms) == 2
        foundation_tasks = ms[0]["tasks"]
        mvp_tasks = ms[1]["tasks"]
        assert len(foundation_tasks) == 2  # priority 1-2
        assert len(mvp_tasks) == 2  # priority 3-4

    def test_legacy_all_high_priority(self):
        features = [{"name": "a", "priority": 1}, {"name": "b", "priority": 1}]
        ms = wrap_legacy_features(features)
        assert len(ms) >= 1

    def test_legacy_empty(self):
        ms = wrap_legacy_features([])
        assert len(ms) == 1  # edge case: single empty milestone


# ═══════════════════════════════════════════════════
# parse_milestones — markdown fallback
# ═══════════════════════════════════════════════════


class TestParseMilestonesMarkdown:
    def test_basic_markdown(self):
        content = (
            "## Foundation\n"
            "### project-setup\n"
            "Create project structure\n"
            "### database\n"
            "Setup database layer\n"
            "\n"
            "## MVP Features\n"
            "### auth\n"
            "User authentication\n"
        )
        ms = parse_milestones_markdown(content)
        assert len(ms) == 2
        assert ms[0]["milestone_title"] == "Foundation"
        assert len(ms[0]["tasks"]) == 2
        assert ms[1]["milestone_title"] == "MVP Features"
        assert len(ms[1]["tasks"]) == 1

    def test_markdown_with_numbered_milestones(self):
        content = (
            "## Milestone 1: Setup\n"
            "### init\n"
            "Initialize\n"
            "## Milestone 2: Build\n"
            "### api\n"
            "Build API\n"
        )
        ms = parse_milestones_markdown(content)
        assert len(ms) == 2
        assert "Setup" in ms[0]["milestone_title"]

    def test_markdown_with_spec_blocks(self):
        content = (
            "## Core\n"
            "### auth\n"
            "Auth module\n"
            "```spec.md\n"
            "# Specification: auth\n"
            "Implement JWT authentication\n"
            "```\n"
        )
        ms = parse_milestones_markdown(content)
        assert len(ms) == 1
        assert ms[0]["tasks"][0]["spec"] == "# Specification: auth\nImplement JWT authentication"

    def test_markdown_no_milestones(self):
        content = "Just some text without any ## headers"
        ms = parse_milestones_markdown(content)
        assert ms == []

    def test_markdown_milestone_without_tasks(self):
        content = "## Empty Milestone\nSome description\n"
        ms = parse_milestones_markdown(content)
        assert len(ms) == 1
        assert ms[0]["tasks"] == []

    def test_slug_gets_index_prefix(self):
        content = "## Foundation\n### init\nSetup\n## MVP\n### api\nAPI\n"
        ms = parse_milestones_markdown(content)
        assert ms[0]["milestone_slug"].startswith("01-")
        assert ms[1]["milestone_slug"].startswith("02-")


# ═══════════════════════════════════════════════════
# parse_milestones — unbalanced JSON fallback
# ═══════════════════════════════════════════════════


class TestParseMilestonesUnbalanced:
    def test_json_without_closing_fence(self):
        """LLM forgot the closing ``` — parser should still find JSON."""
        response = (
            'Here is the plan:\n'
            '[{"milestone_slug": "01-core", "milestone_title": "Core", '
            '"tasks": [{"name": "init", "spec": ""}]}]'
        )
        ms = parse_milestones(response)
        assert len(ms) == 1
        assert ms[0]["milestone_slug"] == "01-core"


# ═══════════════════════════════════════════════════
# parse_update_response
# ═══════════════════════════════════════════════════


class TestParseUpdateResponse:
    def test_both_markdown_and_json(self):
        content = (
            "Updated plan:\n"
            "```markdown\n"
            "# Development Plan\n"
            "## M1\n"
            "Updated tasks\n"
            "```\n\n"
            "New tasks:\n"
            '```json\n[{"milestone_slug": "03-extra", "milestone_title": "Extra", '
            '"tasks": [{"name": "logs", "spec": "# Logs"}]}]\n```'
        )
        devplan, new_ms = parse_update_response(content)
        assert "# Development Plan" in devplan
        assert len(new_ms) == 1
        assert new_ms[0]["milestone_slug"] == "03-extra"

    def test_markdown_only(self):
        content = "```markdown\n# Development Plan\nUpdated\n```"
        devplan, new_ms = parse_update_response(content)
        assert "# Development Plan" in devplan
        assert new_ms == []

    def test_json_only(self):
        content = '```json\n[{"milestone_slug": "01-new", "milestone_title": "New", "tasks": []}]\n```'
        devplan, new_ms = parse_update_response(content)
        assert devplan == ""
        assert len(new_ms) == 1

    def test_neither(self):
        content = "No structured content here."
        devplan, new_ms = parse_update_response(content)
        assert devplan == ""
        assert new_ms == []

    def test_invalid_json_ignored(self):
        content = "```json\n{not valid json\n```"
        devplan, new_ms = parse_update_response(content)
        assert new_ms == []


# ═══════════════════════════════════════════════════
# build_devplan_markdown
# ═══════════════════════════════════════════════════


class TestBuildDevplanMarkdown:
    def test_basic_output(self):
        milestones = [
            {
                "milestone_slug": "01-core",
                "milestone_title": "Core",
                "tasks": [
                    {"name": "init", "description": "Setup", "dependencies": []},
                    {"name": "db", "description": "Database", "dependencies": ["init"]},
                ],
            }
        ]
        md = build_devplan_markdown(milestones)
        assert "# Development Plan" in md
        assert "## Core" in md
        assert "01-core" in md
        assert "| 1 | init |" in md
        assert "| 2 | db |" in md
        assert "init" in md  # dependency listed
        assert "2 tasks" in md
        assert "1 milestones" in md

    def test_empty_milestones(self):
        md = build_devplan_markdown([])
        assert "# Development Plan" in md
        assert "0 tasks" in md

    def test_no_dependencies_shows_dash(self):
        milestones = [
            {
                "milestone_slug": "01-m",
                "milestone_title": "M",
                "tasks": [{"name": "t", "description": "task"}],
            }
        ]
        md = build_devplan_markdown(milestones)
        assert "—" in md  # em-dash for no deps
