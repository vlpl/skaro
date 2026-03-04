"""Shared utilities for plan parsing across phases."""

from __future__ import annotations


def count_plan_stages(plan: str) -> int:
    """Count ``## Stage N`` / ``## Этап N`` headings in a plan document.

    Returns 0 when no stage headings are found.
    """
    count = 0
    for line in plan.splitlines():
        s = line.strip().lower()
        if s.startswith(("#", "##")) and any(w in s for w in ["stage", "этап"]):
            count += 1
    return count
