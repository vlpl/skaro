"""Token tracking: cumulative usage in YAML + detailed JSONL log."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from skaro_core.config._models import SKARO_DIR, TOKENS_FILENAME, USAGE_LOG_FILENAME


def _tokens_path(project_root: Path | None = None) -> Path:
    import skaro_core.config as _cfg

    root = project_root or _cfg.find_project_root() or Path.cwd()
    return root / SKARO_DIR / TOKENS_FILENAME


def _usage_log_path(project_root: Path | None = None) -> Path:
    import skaro_core.config as _cfg

    root = project_root or _cfg.find_project_root() or Path.cwd()
    return root / SKARO_DIR / USAGE_LOG_FILENAME


def load_token_usage(project_root: Path | None = None) -> dict[str, int]:
    """Load cumulative token usage stats."""
    path = _tokens_path(project_root)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return {
                "total_tokens": data.get("total_tokens", 0),
                "prompt_tokens": data.get("prompt_tokens", 0),
                "completion_tokens": data.get("completion_tokens", 0),
            }
    return {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}


def add_token_usage(
    usage: dict[str, int],
    project_root: Path | None = None,
    *,
    phase: str = "",
    task: str = "",
    model: str = "",
    provider: str = "",
    role: str = "",
    feature: str = "",
) -> dict[str, int]:
    """Add token usage from an LLM response to cumulative totals and JSONL log."""
    if not usage:
        return load_token_usage(project_root)

    resolved_task = task or feature

    input_tok = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
    output_tok = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)

    # Update cumulative totals
    current = load_token_usage(project_root)
    current["total_tokens"] += usage.get("total_tokens", 0) or (input_tok + output_tok)
    current["prompt_tokens"] += input_tok
    current["completion_tokens"] += output_tok

    path = _tokens_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(current, f, default_flow_style=False)

    # Append detailed entry to JSONL log
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "task": resolved_task,
        "feature": resolved_task,
        "model": model,
        "provider": provider,
        "role": role,
        "input_tokens": input_tok,
        "output_tokens": output_tok,
    }
    log_path = _usage_log_path(project_root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return current


def load_usage_log(project_root: Path | None = None) -> list[dict]:
    """Load all entries from usage_log.jsonl."""
    path = _usage_log_path(project_root)
    entries: list[dict] = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return entries
