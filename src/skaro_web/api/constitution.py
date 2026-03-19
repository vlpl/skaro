"""Constitution endpoints."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from skaro_core.artifacts import ArtifactManager, TEMPLATES_PKG_DIR
from skaro_core.config import load_config, save_config
from skaro_core.phases.base import strip_outer_md_fence
from skaro_web.api.deps import broadcast, get_am, get_project_root, get_ws_manager, llm_phase
from skaro_web.api.schemas import ContentBody, ConstitutionSaveBody

router = APIRouter(prefix="/api/constitution", tags=["constitution"])

# ── Presets directory (ships with the package) ─────
_PRESETS_DIR = TEMPLATES_PKG_DIR / "constitution-presets" if TEMPLATES_PKG_DIR else None

# Registry: id → (label, category, filename)
_PRESET_REGISTRY: list[dict[str, str]] = [
    {"id": "react",        "name": "React",        "category": "frontend", "file": "react.md"},
    {"id": "vue",          "name": "Vue.js",       "category": "frontend", "file": "vue.md"},
    {"id": "sveltekit",    "name": "SvelteKit",    "category": "frontend", "file": "sveltekit.md"},
    {"id": "nextjs",       "name": "Next.js",      "category": "frontend", "file": "nextjs.md"},
    {"id": "angular",      "name": "Angular",      "category": "frontend", "file": "angular.md"},
    {"id": "fastapi",      "name": "FastAPI",       "category": "backend",  "file": "fastapi.md"},
    {"id": "django",       "name": "Django",        "category": "backend",  "file": "django.md"},
    {"id": "express",      "name": "Express.js",    "category": "backend",  "file": "express.md"},
    {"id": "nestjs",       "name": "NestJS",        "category": "backend",  "file": "nestjs.md"},
    {"id": "react-native", "name": "React Native",  "category": "mobile",   "file": "react-native.md"},
    {"id": "flutter",      "name": "Flutter",       "category": "mobile",   "file": "flutter.md"},
    {"id": "kotlin-mp",    "name": "Kotlin MP",     "category": "mobile",   "file": "kotlin-mp.md"},
]


@router.get("")
async def get_constitution(am: ArtifactManager = Depends(get_am)):
    return {
        "content": am.read_constitution(),
        "has_constitution": am.has_constitution,
        "validation": am.validate_constitution(),
    }


@router.post("/validate")
async def validate_constitution(
    request: Request,
    am: ArtifactManager = Depends(get_am),
    project_root: Path = Depends(get_project_root),
):
    """Validate Constitution and auto-add missing sections."""
    from skaro_core.llm.base import LLMMessage, create_llm_adapter
    from skaro_core.config import load_config

    result = am.validate_constitution()
    is_valid = all(result.values()) if result else False

    if is_valid:
        am.mark_constitution_validated()
        return {"success": True, "valid": True, "checks": result}

    # Если есть缺失ющие разделы - добавляем их через LLM
    missing_sections = [key for key, value in result.items() if not value]

    if missing_sections:
        current_content = am.read_constitution()

        # Загружаем промт для добавления разделов (используем существующий или создаём простой)
        prompt = f"""Доработай Конституцию, добавив缺失ствующие разделы.

Текущая Конституция:
{current_content}

缺失ствующие разделы (добавь их в конец документа):
{', '.join(missing_sections)}

Для каждого缺失ствующего раздела:
1. Добавь заголовок уровня ## (например, ## 6. LLM Rules)
2. Напиши 2-3 предложения с рекомендациями для этого раздела
3. Используй форматирование Markdown

Верни полный текст обновлённой Конституции.
""".strip()

        try:
            config = load_config(project_root)
            llm_config = config.llm_for_phase("analytics")
            llm = create_llm_adapter(llm_config)

            messages = [LLMMessage(role="user", content=prompt)]
            response = await llm.complete(messages)
            new_constitution = strip_outer_md_fence(response.content)

            # Сохраняем обновлённую Конституцию
            am.write_constitution(new_constitution)

            # Обновляем validation
            result = am.validate_constitution()
            is_valid = all(result.values()) if result else False

            if is_valid:
                am.mark_constitution_validated()

            await broadcast(request, {"event": "artifact:updated", "artifact": "constitution"})

            return {
                "success": True,
                "valid": is_valid,
                "checks": result,
                "auto_added": missing_sections,
                "message": f"Добавлены разделы: {', '.join(missing_sections)}",
            }

        except Exception as e:
            # Если LLM неудачно - просто возвращаем результат валидации
            return {
                "success": True,
                "valid": False,
                "checks": result,
                "error": str(e),
                "missing": missing_sections,
            }

    return {"success": True, "valid": is_valid, "checks": result}


@router.put("")
async def save_constitution(
    request: Request,
    payload: ConstitutionSaveBody,
    am: ArtifactManager = Depends(get_am),
    project_root: Path = Depends(get_project_root),
):
    am.write_constitution(payload.content)
    am.generate_project_gitignore(payload.content)

    # Link skills preset when a preset_id is provided
    if payload.preset_id is not None:
        config = load_config(project_root)
        config.skills.preset = payload.preset_id
        # Reset disabled list when switching presets
        config.skills.disabled = []
        save_config(config, project_root)

    await broadcast(request, {"event": "artifact:updated", "artifact": "constitution"})
    return {"success": True}


@router.get("/presets")
async def list_presets():
    """Return list of available constitution presets (metadata only)."""
    return {"presets": _PRESET_REGISTRY}


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Return the full markdown content for a specific preset."""
    entry = next((p for p in _PRESET_REGISTRY if p["id"] == preset_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    if _PRESETS_DIR is None:
        raise HTTPException(status_code=500, detail="Templates directory not found")
    path = _PRESETS_DIR / entry["file"]
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Preset file missing: {entry['file']}")
    return {"id": preset_id, "content": path.read_text(encoding="utf-8")}


@router.post("/populate-from-requirements")
async def populate_constitution_from_requirements(
    request: Request,
    am: ArtifactManager = Depends(get_am),
    project_root: Path = Depends(get_project_root),
    ws: ConnectionManager = Depends(get_ws_manager),
):
    """Populate/update Constitution based on accepted requirements."""
    from skaro_core.phases.analytics import AnalyticsPhase
    import re

    # Чтение требований
    requirements_dir = am.skaro / "requirements"
    if not requirements_dir.exists():
        return {"success": False, "message": "Requirements directory not found"}

    accepted_reqs = []
    for jf in requirements_dir.glob("*.json"):
        try:
            meta = json.loads(jf.read_text(encoding='utf-8'))
            if meta.get('status') == 'accepted':
                rid = jf.stem
                mdf = jf.with_suffix('.md')
                content = mdf.read_text(encoding='utf-8') if mdf.exists() else ''
                tm = re.match(r'^#\s*(.+?)$', content, re.MULTILINE)
                accepted_reqs.append({
                    'id': rid, 'type': meta.get('type', 'FR'),
                    'title': tm.group(1).strip() if tm else rid,
                    'content': content.strip()
                })
        except Exception:
            continue

    if not accepted_reqs:
        return {"success": False, "message": "No accepted requirements found"}

    # Запускаем через llm_phase для красивого вывода
    phase = AnalyticsPhase(project_root=project_root)
    async with llm_phase(ws, "constitution-populate", phase, request=request):
        # Готовим контекст
        constitution = am.read_constitution() or "Конституция пуста"
        prompt_path = Path(__file__).parent.parent.parent / "skaro_core" / "prompts" / "constitution-populate.md"
        prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        req_text = "\n\n".join([f"### {r['id']}: {r['title']}\n{r['content']}" for r in accepted_reqs])
        context = f"## Требования\n\n{req_text}\n\n## Конституция\n\n{constitution}"

        # Вызов LLM через фазу
        result = await phase._populate_constitution(prompt, context, accepted_reqs)

    await ws.broadcast({"event": "phase:completed", "phase": "constitution"})

    if result.success:
        am.write_constitution(result.data.get('constitution', ''))
        await broadcast(request, {"event": "artifact:updated", "artifact": "constitution"})
        return {"success": True, "message": f"Updated from {len(accepted_reqs)} requirements"}
    return {"success": False, "message": result.message}
