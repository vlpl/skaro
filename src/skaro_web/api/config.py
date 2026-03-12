"""Configuration endpoints.

Secrets handling is transparent to the frontend:
- GET returns the resolved ``api_key`` so the eye-toggle in UI works.
- PUT accepts a plaintext ``api_key``; the backend saves it to
  ``.skaro/secrets.yaml`` and stores only the env-var name in ``config.yaml``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request

from skaro_core.config import (
    ROLE_PHASES,
    SkaroConfig,
    load_config,
    save_config,
    save_secret,
)
from skaro_core.llm.base import PROVIDER_PRESETS
from skaro_core.providers import get_model_ids, get_provider_keys, get_providers
from skaro_web.api.deps import broadcast, get_project_root
from skaro_web.api.schemas import ConfigUpdateBody

router = APIRouter(prefix="/api/config", tags=["config"])


# ── Helpers ──────────────────────────────────────────────

def _env_name_for_provider(provider: str) -> str:
    """Determine the canonical env-var name for a provider."""
    preset = PROVIDER_PRESETS.get(provider)
    if preset and preset[1]:
        return preset[1]
    return f"{provider.upper()}_API_KEY"


def _config_to_frontend(config: SkaroConfig) -> dict:
    """Serialize config for frontend with resolved API keys."""
    data = config.to_dict()

    # Replace internal api_key_env with resolved api_key for frontend
    llm = data.get("llm", {})
    llm.pop("api_key_env", None)
    llm["api_key"] = config.llm.api_key or ""

    for rname, rd in data.get("roles", {}).items():
        if rd and isinstance(rd, dict):
            rd.pop("api_key_env", None)
            rc = config.roles.get(rname)
            if rc and rc.is_active:
                role_llm = config.llm_for_role(rname)
                rd["api_key"] = role_llm.api_key or ""
            else:
                rd["api_key"] = ""

    return data


# ── Endpoints ────────────────────────────────────────────

@router.get("")
async def get_config(project_root: Path = Depends(get_project_root)):
    config = load_config(project_root)
    data = _config_to_frontend(config)
    all_providers = get_providers()
    data["_provider_presets"] = {
        k: {
            "name": all_providers[k].name if k in all_providers else k,
            "model": v[0],
            "api_key_env": v[1],
            "needs_key": v[2],
            "models": get_model_ids(k),
        }
        for k, v in PROVIDER_PRESETS.items()
    }
    data["_provider_keys"] = get_provider_keys()
    data["_role_phases"] = ROLE_PHASES
    return data


@router.put("")
async def update_config(
    request: Request,
    payload: ConfigUpdateBody,
    project_root: Path = Depends(get_project_root),
):
    raw = payload.to_dict()
    existing = load_config(project_root)

    # ── Extract and save API keys to secrets.yaml ──
    llm_raw = raw.get("llm", {})
    api_key = llm_raw.pop("api_key", None)
    provider = llm_raw.get("provider", "anthropic")

    if api_key:
        env_name = _env_name_for_provider(provider)
        save_secret(env_name, api_key, project_root)
        llm_raw["api_key_env"] = env_name
    else:
        llm_raw["api_key_env"] = existing.llm.api_key_env

    for rname, rd in raw.get("roles", {}).items():
        if rd and isinstance(rd, dict):
            role_key = rd.pop("api_key", None)
            if role_key:
                role_provider = rd.get("provider", provider)
                role_env = _env_name_for_provider(role_provider)
                save_secret(role_env, role_key, project_root)
                rd["api_key_env"] = role_env
            else:
                existing_role = existing.roles.get(rname)
                rd["api_key_env"] = existing_role.api_key_env if existing_role else None

    config = SkaroConfig.from_dict(raw)
    save_config(config, project_root)
    await broadcast(request, {"event": "config:updated"})
    return {"success": True}
