"""Architecture review phase."""

from __future__ import annotations

import json
import re
from datetime import date as _date
from typing import Any

from skaro_core.phases.base import BasePhase, PhaseResult


# Marker that separates review from proposed architecture in LLM response.
_PROPOSED_HEADING_RE = re.compile(
    r"^##\s+Proposed\s+Architecture", re.IGNORECASE | re.MULTILINE
)


class ArchitecturePhase(BasePhase):
    phase_name = "architecture"

    async def run(self, feature: str | None = None, **kwargs: Any) -> PhaseResult:
        architecture_draft = kwargs.get("architecture_draft", "")
        domain_description = kwargs.get("domain_description", "")

        if not architecture_draft:
            return PhaseResult(
                success=False,
                message="Architecture draft is required. Pass it as architecture_draft.",
            )

        prompt_template = self._load_prompt_template("architecture")
        if prompt_template:
            prompt = prompt_template.replace(
                "{domain_description}", domain_description or "(not provided)"
            ).replace(
                "{architecture_draft}", architecture_draft
            )
        else:
            prompt = (
                f"Review this architecture as a senior architect.\n\n"
                f"Domain: {domain_description}\n\n"
                f"Architecture draft:\n{architecture_draft}\n\n"
                f"Provide your response in two sections:\n"
                f"## Review\n<risks, recommendations>\n\n"
                f"## Proposed Architecture\n<full improved architecture document>"
            )

        messages = self._build_messages(prompt)
        response_content = await self._stream_collect(messages)

        review_text, proposed_text = self._split_response(response_content)

        # Persist the review result so it survives page reloads.
        self.artifacts.write_architecture_review(review_text)

        return PhaseResult(
            success=True,
            message=review_text,
            data={
                "proposed_architecture": proposed_text,
            },
        )

    async def apply_review(self, architecture: str, review: str) -> str:
        """Apply review recommendations: LLM rewrites architecture.

        Returns the proposed architecture text.
        """
        prompt_template = self._load_prompt_template("architecture-apply")
        if prompt_template:
            prompt = prompt_template
        else:
            prompt = (
                "Apply review recommendations to this architecture.\n\n"
                "## Current Architecture\n{architecture}\n\n"
                "## Review\n{review}\n\n"
                "Return the complete improved architecture document."
            )

        prompt = prompt.replace("{architecture}", architecture).replace("{review}", review)
        messages = self._build_messages(prompt)
        response = await self._stream_collect(messages)
        return response.strip()

    async def generate_adrs(
        self,
        architecture: str,
        review: str = "",
        adr_template: str = "",
    ) -> list[dict[str, str]]:
        """Generate ADR proposals from architecture using LLM.

        Returns a list of ``{"title": ..., "content": ...}`` dicts.
        Raises ValueError if LLM response cannot be parsed as JSON.
        """
        prompt_template = self._load_prompt_template("adr-generate")
        if prompt_template:
            prompt = prompt_template
        else:
            prompt = (
                "Generate ADRs for this architecture. Return JSON array with "
                "number, title, content fields.\n\nArchitecture:\n{architecture}"
            )

        today = _date.today().isoformat()
        review_section = f"Architecture review feedback:\n{review}" if review.strip() else ""
        prompt = (
            prompt
            .replace("{architecture}", architecture)
            .replace("{review_section}", review_section)
            .replace("{adr_template}", adr_template)
            .replace("{today}", today)
        )

        messages = self._build_messages(prompt)
        response = await self._stream_collect(messages)

        json_match = re.search(r"```json\s*\n([\s\S]*?)\n\s*```", response)
        if not json_match:
            raise ValueError(f"LLM did not return valid JSON.\n{response}")

        return json.loads(json_match.group(1))

    @staticmethod
    def _split_response(content: str) -> tuple[str, str]:
        """Split LLM response into (review, proposed_architecture).

        Looks for '## Proposed Architecture' heading.  Everything before it
        is the review; everything after (including the heading) is the
        proposed architecture body (heading stripped).
        """
        match = _PROPOSED_HEADING_RE.search(content)
        if not match:
            # LLM didn't follow format — treat entire response as review.
            return content.strip(), ""

        review = content[: match.start()].strip()
        # Strip the heading itself from the proposed section.
        proposed_raw = content[match.end() :].strip()
        return review, proposed_raw
