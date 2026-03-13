"""Skill dataclass — a single loadable skill definition."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Skill:
    """A single skill loaded from YAML."""

    name: str
    description: str = ""
    version: str = ""
    phases: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    instructions: str = ""
    phase_instructions: dict[str, str] = field(default_factory=dict)
    source: str = ""  # "preset", "global", "user"

    def applies_to(self, phase: str, role: str | None) -> bool:
        """Check if this skill applies to the given phase and role."""
        if self.phases and phase not in self.phases:
            return False
        if self.roles and role and role not in self.roles:
            return False
        return True

    def get_instructions(self, phase: str) -> str:
        """Return phase-specific instructions if available, else general."""
        return self.phase_instructions.get(phase, "") or self.instructions

    @classmethod
    def from_dict(cls, data: dict, source: str = "") -> Skill:
        """Create a Skill from a parsed YAML dict."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=str(data.get("version", "")),
            phases=data.get("phases") or [],
            roles=data.get("roles") or [],
            instructions=data.get("instructions", ""),
            phase_instructions=data.get("phase_instructions") or {},
            source=source,
        )
