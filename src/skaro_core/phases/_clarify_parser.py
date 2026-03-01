"""Parse raw LLM clarification output into structured questions with options."""

from __future__ import annotations

import json
import re


def parse_raw_questions(text: str) -> list[dict]:
    """Parse LLM output into list of {question, context, options}.

    Expects JSON array. Falls back to legacy numbered-question parsing.
    Returns list of dicts with keys: question, context, options.
    """
    parsed = _try_parse_json(text)
    if parsed:
        return parsed

    # Fallback: legacy numbered format → convert to structured
    return _parse_legacy(text)


def _try_parse_json(text: str) -> list[dict] | None:
    """Try to extract and parse JSON array from text."""
    # Strip markdown fences if present
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", stripped)
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    stripped = stripped.strip()

    # Find JSON array boundaries
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        data = json.loads(stripped[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, list) or len(data) == 0:
        return None

    result = []
    for item in data:
        if not isinstance(item, dict) or "question" not in item:
            continue
        result.append({
            "question": str(item.get("question", "")),
            "context": str(item.get("context", "")),
            "options": [str(o) for o in item.get("options", []) if o],
        })

    return result if result else None


def _parse_legacy(text: str) -> list[dict]:
    """Fallback: parse numbered questions from freeform LLM text."""
    questions: list[dict] = []
    current_lines: list[str] = []
    in_question = False

    pattern = re.compile(
        r"^(?:\*{0,2}\s*(?:Question\s+|Q)\d+[\s:.)\\*]|\*{0,2}\d+[\s:.)\\*])",
        re.IGNORECASE,
    )

    for line in text.splitlines():
        stripped = line.strip()
        if pattern.match(stripped):
            if current_lines and in_question:
                questions.append({
                    "question": "\n".join(current_lines).strip(),
                    "context": "",
                    "options": [],
                })
            current_lines = [line]
            in_question = True
        elif in_question:
            current_lines.append(line)

    if current_lines and in_question:
        questions.append({
            "question": "\n".join(current_lines).strip(),
            "context": "",
            "options": [],
        })

    return questions
