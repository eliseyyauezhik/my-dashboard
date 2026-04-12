#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote


DEFAULT_ARCHIVE_DOCS = Path(
    r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\AI_Workspace\project_archive\antigravity\my_dashboard\docs"
)
DEFAULT_ARCHIVE_REPORTS = Path(
    r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\AI_Workspace\project_archive\_migration_reports"
)
DEFAULT_OBSIDIAN_ROOT = Path(r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase")
DEFAULT_PROFILE_CONFIG = Path("config/personal_system_profile.json")
DEFAULT_TELEGRAM_INTELLIGENCE = Path("data/telegram_intelligence.json")
DEFAULT_MANUAL_BASE = "projects_manual_base.json"
DEFAULT_PROJECTS_OUT = "projects.json"
NOTEBOOKLM_AVAILABLE = os.getenv("NOTEBOOKLM_AVAILABLE", "false").strip().lower() == "true"

TOPIC_LABELS = {
    "education": "Образование",
    "products": "Продукты",
    "agents": "AI / Агенты",
    "antigravity": "Инфраструктура",
    "business": "Бизнес",
    "configs": "Конфиги",
    "manual": "Ручные проекты",
}

STATUS_RU = {
    "active": "В работе",
    "paused": "Пауза",
    "research": "Исследование",
    "backlog": "Бэклог",
    "done": "Готово",
}

DEFAULT_SYSTEM_PROFILE: dict[str, Any] = {
    "title": "Системная карта интересов",
    "summary": "Личная операционная система для маршрутизации входящей информации в проекты, навыки, решения и архив.",
    "roles": [],
    "lifeAreas": [],
    "focusThemes": [],
    "interestSignals": [],
    "noiseFilters": [],
    "reviewCadence": {},
    "monitoringSources": [],
    "processingProtocol": [],
    "routingRules": [],
    "bestPracticeRecommendations": [],
    "priorityProjects": [],
    "skillCandidates": [],
    "projectHypotheses": [],
    "projectTitleTranslations": {},
}

DEFAULT_PROJECT_TITLE_TRANSLATIONS = {
    "ai agent core workspace": "Основное рабочее пространство ИИ-агента",
    "antigravity dashboard prototype": "Прототип дашборда Antigravity",
    "antigravity dashboard workspace": "Рабочее пространство дашборда Antigravity",
    "appscout": "Разведка приложений",
    "davydov phantom": "Фантом Давыдова",
    "grant presentation": "Грантовая презентация",
    "gymnasium landing": "Лендинг гимназии",
    "interactive panels rating": "Рейтинг интерактивных панелей",
    "kora strategy": "Стратегия КОРА",
    "smartmeeting backend": "Умное совещание: сервер",
    "smartmeeting web": "Умное совещание: веб-интерфейс",
    "tech radar skill": "Навык Tech Radar",
    "tgaggregator": "Telegram-агрегатор",
    "agent second brain": "Второй мозг агента",
    "agent second brain (recovered fragments)": "Второй мозг агента: восстановленные фрагменты",
    "skills": "Навыки",
    "smartmeeting": "Умное совещание",
}

PROJECT_TITLE_TOKEN_TRANSLATIONS = {
    "ai": "ИИ",
    "agent": "агент",
    "agents": "агенты",
    "antigravity": "Antigravity",
    "app": "приложение",
    "apps": "приложения",
    "backend": "сервер",
    "brain": "мозг",
    "core": "основное",
    "dashboard": "дашборд",
    "education": "образование",
    "grant": "грант",
    "interactive": "интерактивные",
    "landing": "лендинг",
    "panels": "панели",
    "phantom": "фантом",
    "presentation": "презентация",
    "rating": "рейтинг",
    "second": "второй",
    "skill": "навык",
    "smartmeeting": "умное совещание",
    "strategy": "стратегия",
    "tech": "tech",
    "tg": "telegram",
    "web": "веб-интерфейс",
    "workspace": "рабочее пространство",
}


ROUTE_LABELS = {
    "project_update": "Обновить проект",
    "skill_candidate": "Кандидат в навык",
    "project_hypothesis": "Проектная гипотеза",
    "reference_note": "Заметка в базе",
    "archive": "Архив",
}

THEME_LABELS = {
    "knowledge": "База знаний",
    "agents": "Агентные системы",
    "education": "Образование",
    "family": "Семья и дом",
    "media": "Медиа и контент",
    "product": "Продукты и сервисы",
    "research": "Исследование",
    "general": "Общий контур",
}

LIFE_AREA_FALLBACK_LABELS = {
    "я": "Я",
    "семья": "Семья",
    "работа": "Работа",
}

PROJECT_HINT_RULES: list[tuple[str, tuple[str, ...]]] = [
    (r"(notebooklm|nlm\b|mcp\b|mcp-config|mcp_config|batchexecute|google notebooklm)", ("ai-agent-core-workspace", "antigravity-dashboard-workspace")),
    (r"(obsidian|knowledge hub|knowledge base|vault|kb\b|база знаний|библиотека знаний)", ("ai-agent-core-workspace", "system-interest-map", "antigravity-dashboard-workspace")),
    (r"(dashboard|дашборд|meta-system|мета-систем|architecture|архитектур|antigravity)", ("antigravity-dashboard-workspace", "system-interest-map", "ai-agent-core-workspace")),
    (r"(grant|грант|presentation|презентац|архитектор развития)", ("grant-presentation",)),
    (r"(gymnasium|гимнази|website|landing|лендинг|site update|visual and content)", ("gymnasium-landing",)),
    (r"(davydov|давыдов)", ("davydov-phantom",)),
    (r"(\bkora\b|кора|business system|digital transformation strategic)", ("kora-strategy",)),
    (r"(monitoring|news|n8n|youtube|video|идеи из видео|ai news)", ("interest-monitoring-loop", "tgaggregator")),
]


@dataclass
class SourceBundle:
    projects_index: Path
    workflows_index: Path
    chats_index: Path
    organization_audit: Path
    base_projects_json: Path
    obsidian_root: Path
    out_dashboard_json: Path
    out_mindmap_json: Path
    out_projects_json: Path
    out_project_registry_json: Path


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    parts = [p.strip().strip("`") for p in value.split(";")]
    seen: set[str] = set()
    items: list[str] = []
    for part in parts:
        if not part:
            continue
        if part not in seen:
            seen.add(part)
            items.append(part)
    return items


def to_bool(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def normalize_path(value: str | None) -> str:
    if not value:
        return ""
    clean = value.strip().strip("`").replace("/", "\\")
    clean = re.sub(r"\\+", "\\\\", clean)
    return clean.lower()


def is_specific_path(value: str | None) -> bool:
    if not value:
        return False
    p = normalize_path(value)
    if not re.match(r"^[a-z]:\\", p):
        return False
    parts = [x for x in p.split("\\") if x and not re.match(r"^[a-z]:$", x)]
    return len(parts) >= 2


def path_related(a: str | None, b: str | None) -> bool:
    na = normalize_path(a)
    nb = normalize_path(b)
    if not na or not nb:
        return False
    if not is_specific_path(na) or not is_specific_path(nb):
        return False
    if len(na) < 8 or len(nb) < 8:
        return False
    return na in nb or nb in na


def slugify(value: str, fallback: str = "item") -> str:
    v = value.strip().lower()
    v = re.sub(r"[^\wа-яё]+", "-", v, flags=re.IGNORECASE)
    v = re.sub(r"-{2,}", "-", v).strip("-")
    return v or fallback


def safe_filename(value: str, fallback: str = "note") -> str:
    name = slugify(value, fallback=fallback)
    name = re.sub(r"[<>:\"/\\|?*]", "-", name)
    name = name.strip(". ")
    if not name:
        name = fallback
    return name[:96]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def merge_dicts(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def unique_nonempty_text(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str):
            parts = split_semicolon(value)
        else:
            parts = [str(value or "").strip()]
        for text in parts:
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
    return result


def join_unique_notes(*values: Any) -> str:
    return " ; ".join(unique_nonempty_text(list(values)))


def ensure_manual_base_seeded(manual_base_path: Path, generated_projects_path: Path) -> None:
    if manual_base_path.exists():
        return
    payload: dict[str, Any] = {
        "meta": {
            "version": "1.0-manual-base",
            "seededAt": datetime.now().isoformat(timespec="seconds"),
            "generated": False,
        },
        "projects": [],
        "ideas": [],
        "upgradePaths": [],
    }
    if generated_projects_path.exists() and manual_base_path.resolve() != generated_projects_path.resolve():
        legacy = read_json(generated_projects_path, {})
        if isinstance(legacy, dict):
            payload["projects"] = legacy.get("projects", []) if isinstance(legacy.get("projects"), list) else []
            payload["ideas"] = legacy.get("ideas", []) if isinstance(legacy.get("ideas"), list) else []
            payload["upgradePaths"] = (
                legacy.get("upgradePaths", []) if isinstance(legacy.get("upgradePaths"), list) else []
            )
            payload["meta"]["seededFrom"] = str(generated_projects_path)
    write_json(manual_base_path, payload)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    lines = text.splitlines()
    frontmatter: dict[str, Any] = {}
    index = 1
    while index < len(lines):
        line = lines[index]
        index += 1
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            continue
        if value.startswith('"') and value.endswith('"'):
            parsed: Any = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            parsed = value[1:-1]
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        elif re.fullmatch(r"-?\d+", value):
            parsed = int(value)
        else:
            parsed = value
        frontmatter[key] = parsed
    body = "\n".join(lines[index:]).lstrip("\n")
    return frontmatter, body


def parse_markdown_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"_root": []}
    current = "_root"
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def parse_markdown_tasks(lines: list[str]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for raw in lines:
        match = re.match(r"^\s*-\s*\[( |x|X)\]\s*(.+?)\s*$", raw)
        if not match:
            continue
        tasks.append({"task": match.group(2).strip(), "done": match.group(1).strip().lower() == "x"})
    return tasks


def parse_wikilinks(lines: list[str]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"\[\[([^\]|#]+)", "\n".join(lines)):
        note_name = match.group(1).strip()
        key = note_name.casefold()
        if note_name and key not in seen:
            seen.add(key)
            names.append(note_name)
    return names


def first_heading(body: str) -> str:
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def section_text(sections: dict[str, list[str]], name: str) -> str:
    lines = [line.strip() for line in sections.get(name, []) if line.strip()]
    return "\n".join(lines).strip()


def build_obsidian_uri(vault_name: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    return f"obsidian://open?vault={quote(vault_name)}&file={quote(normalized)}"


def build_note_ref(record: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(record["id"]),
        "title": str(record.get("title") or record.get("noteName") or record["id"]),
        "noteName": str(record["noteName"]),
        "notePath": str(record["notePath"]),
        "relativePath": str(record["relativePath"]),
        "obsidianUri": str(record["obsidianUri"]),
    }


def contains_cyrillic(value: str | None) -> bool:
    return bool(value and re.search(r"[А-Яа-яЁё]", value))


def load_obsidian_entities(obsidian_root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    vault_name = obsidian_root.name
    folders = {
        "projects": obsidian_root / "Projects" / "AI Workspace",
        "chats": obsidian_root / "Chats" / "AI Workspace",
        "workflows": obsidian_root / "Workflows" / "AI Workspace",
    }
    result: dict[str, dict[str, dict[str, Any]]] = {
        "projects_by_id": {},
        "projects_by_note": {},
        "chats_by_id": {},
        "chats_by_note": {},
        "workflows_by_id": {},
        "workflows_by_note": {},
    }

    for kind, folder in folders.items():
        if not folder.exists():
            continue
        for note_path in folder.glob("*.md"):
            if note_path.name == "00_INDEX.md":
                continue
            text = note_path.read_text(encoding="utf-8")
            frontmatter, body = parse_frontmatter(text)
            sections = parse_markdown_sections(body)
            note_name = note_path.stem
            record_id = str(frontmatter.get("id") or note_name).strip()
            title = (
                str(frontmatter.get("title") or frontmatter.get("name") or "").strip()
                or first_heading(body)
                or note_name
            )
            relative_path = str(note_path.relative_to(obsidian_root)).replace("\\", "/")
            record = {
                "id": record_id,
                "title": title,
                "noteName": note_name,
                "notePath": note_path,
                "relativePath": relative_path,
                "obsidianUri": build_obsidian_uri(vault_name, relative_path),
                "frontmatter": frontmatter,
                "sections": sections,
                "description": section_text(sections, "Описание"),
                "notes": section_text(sections, "Заметки"),
                "tasks": parse_markdown_tasks(sections.get("Задачи", [])),
                "relatedProjectNoteNames": parse_wikilinks(sections.get("Проекты", [])),
                "relatedChatNoteNames": parse_wikilinks(sections.get("Связанные чаты", [])),
                "relatedWorkflowNoteNames": parse_wikilinks(sections.get("Связанные workflows", [])),
            }
            result[f"{kind}_by_id"][record_id] = record
            result[f"{kind}_by_note"][note_name.casefold()] = record
    return result


def resolve_note_ids(note_names: list[str], note_lookup: dict[str, dict[str, Any]]) -> set[str]:
    resolved: set[str] = set()
    for note_name in note_names:
        record = note_lookup.get(note_name.casefold())
        if record:
            resolved.add(str(record["id"]))
    return resolved


def apply_obsidian_overlays(
    project_items: list[dict[str, Any]],
    chat_items: list[dict[str, Any]],
    workflow_items: list[dict[str, Any]],
    obsidian_root: Path,
) -> dict[str, dict[str, dict[str, Any]]]:
    entities = load_obsidian_entities(obsidian_root)

    for project in project_items:
        record = entities["projects_by_id"].get(project["id"])
        if not record:
            continue
        project["kbNote"] = build_note_ref(record)
        frontmatter = record["frontmatter"]
        if frontmatter.get("title"):
            project["title"] = str(frontmatter["title"]).strip() or project["title"]
        if frontmatter.get("topic"):
            project["topic"] = str(frontmatter["topic"]).strip() or project["topic"]
        if frontmatter.get("status"):
            project["status"] = str(frontmatter["status"]).strip() or project["status"]
        if record.get("description"):
            project["description"] = record["description"]
        if record.get("notes"):
            project["notes"] = join_unique_notes(record["notes"])
        if record.get("tasks"):
            project["keyTasks"] = record["tasks"]
        project["_project_chat_note_names"] = record.get("relatedChatNoteNames", [])
        project["_project_workflow_note_names"] = record.get("relatedWorkflowNoteNames", [])

    for chat in chat_items:
        record = entities["chats_by_id"].get(chat["id"])
        if not record:
            continue
        chat["kbNote"] = build_note_ref(record)
        if record.get("title"):
            chat["title"] = record["title"]
        if record["frontmatter"].get("theme"):
            chat["theme"] = str(record["frontmatter"]["theme"]).strip() or chat["theme"]
        resolved = resolve_note_ids(record.get("relatedProjectNoteNames", []), entities["projects_by_note"])
        if resolved:
            chat["relatedProjectIds"] = sorted(set(chat.get("relatedProjectIds", [])) | resolved)

    for workflow in workflow_items:
        record = entities["workflows_by_id"].get(workflow["id"])
        if not record:
            continue
        workflow["kbNote"] = build_note_ref(record)
        if record.get("title"):
            workflow["name"] = record["title"]
        if record["frontmatter"].get("source"):
            workflow["source"] = str(record["frontmatter"]["source"]).strip() or workflow["source"]
        if record.get("notes"):
            workflow["notes"] = join_unique_notes(record["notes"])
        resolved = resolve_note_ids(record.get("relatedProjectNoteNames", []), entities["projects_by_note"])
        if resolved:
            workflow["relatedProjectIds"] = sorted(set(workflow.get("relatedProjectIds", [])) | resolved)

    project_to_chat_ids: dict[str, set[str]] = defaultdict(set)
    project_to_workflow_ids: dict[str, set[str]] = defaultdict(set)

    for chat in chat_items:
        for project_id in chat.get("relatedProjectIds", []):
            project_to_chat_ids[project_id].add(chat["id"])

    for workflow in workflow_items:
        for project_id in workflow.get("relatedProjectIds", []):
            project_to_workflow_ids[project_id].add(workflow["id"])

    for project in project_items:
        related_chat_ids = set(project.get("relatedChatIds", []))
        related_workflow_ids = set(project.get("relatedWorkflowIds", []))
        related_chat_ids |= project_to_chat_ids.get(project["id"], set())
        related_workflow_ids |= project_to_workflow_ids.get(project["id"], set())
        related_chat_ids |= resolve_note_ids(project.pop("_project_chat_note_names", []), entities["chats_by_note"])
        related_workflow_ids |= resolve_note_ids(
            project.pop("_project_workflow_note_names", []), entities["workflows_by_note"]
        )
        project["relatedChatIds"] = sorted(related_chat_ids)
        project["relatedWorkflowIds"] = sorted(related_workflow_ids)
        project["relatedChatsCount"] = len(project["relatedChatIds"])
        project["relatedWorkflowsCount"] = len(project["relatedWorkflowIds"])

    return entities


def next_project_step(project: dict[str, Any]) -> str:
    for item in project.get("keyTasks", []) or []:
        if isinstance(item, dict) and not item.get("done"):
            return str(item.get("task", "")).strip()
    return "Проверить текущий контекст проекта и выбрать следующий шаг."


def build_project_launch_prompt(
    project: dict[str, Any],
    chat_refs: list[dict[str, str]],
    workflow_refs: list[dict[str, str]],
) -> str:
    lines = [
        f"Проект: {project['title']}",
        f"project_id: {project['id']}",
        f"Статус: {project.get('status', 'research')}",
        f"Тема: {project.get('topic', 'manual')}",
        f"Следующий шаг: {next_project_step(project)}",
    ]
    kb_note = project.get("kbNote")
    if kb_note:
        lines.append(f"KB note: {kb_note.get('relativePath', '')}")
    if project.get("description"):
        lines.append(f"Описание: {summarize_text(project.get('description'), 240)}")
    if chat_refs:
        lines.append("Связанные чаты: " + ", ".join(ref["title"] for ref in chat_refs[:5]))
    if workflow_refs:
        lines.append("Связанные workflows: " + ", ".join(ref["title"] for ref in workflow_refs[:5]))
    lines.extend(
        [
            "Режим работы:",
            "- сначала читать KB note и связанные сущности;",
            "- не создавать новую сущность без проверки связи с существующим проектом;",
            "- результат класть обратно в vault и только затем показывать на dashboard;",
        ]
    )
    return "\n".join(lines)


def build_project_registry(
    projects: list[dict[str, Any]],
    chats: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
    vault_root: Path,
) -> dict[str, Any]:
    chat_by_id = {item["id"]: item for item in chats}
    workflow_by_id = {item["id"]: item for item in workflows}
    registry_items: list[dict[str, Any]] = []

    for project in projects:
        related_chats = [
            build_note_ref(chat["kbNote"])
            if chat.get("kbNote")
            else {"id": chat["id"], "title": chat.get("title", chat["id"])}
            for chat_id in project.get("relatedChatIds", [])
            if (chat := chat_by_id.get(chat_id))
        ]
        related_workflows = [
            build_note_ref(workflow["kbNote"])
            if workflow.get("kbNote")
            else {"id": workflow["id"], "title": workflow.get("name", workflow["id"])}
            for workflow_id in project.get("relatedWorkflowIds", [])
            if (workflow := workflow_by_id.get(workflow_id))
        ]

        allowed_tools = ["vault", "dashboard"]
        if related_chats:
            allowed_tools.append("chat-history")
        if related_workflows:
            allowed_tools.append("workflow-history")
        if NOTEBOOKLM_AVAILABLE:
            allowed_tools.append("notebooklm")

        registry_items.append(
            {
                "id": project["id"],
                "title": project["title"],
                "status": project.get("status", "research"),
                "topic": project.get("topic", "manual"),
                "kbNote": project.get("kbNote"),
                "sourcePath": project.get("sourcePath", ""),
                "destinationPath": project.get("destinationPath", ""),
                "relatedChats": related_chats,
                "relatedWorkflows": related_workflows,
                "projectMode": {
                    "nextStep": next_project_step(project),
                    "allowedTools": allowed_tools,
                    "notebooklmEnabled": NOTEBOOKLM_AVAILABLE,
                    "entryPoints": {
                        "kb": (project.get("kbNote") or {}).get("obsidianUri", ""),
                        "dashboard": f"#project:{project['id']}",
                    },
                },
                "launchContract": {
                    "projectId": project["id"],
                    "nextStep": next_project_step(project),
                    "allowedTools": allowed_tools,
                    "notebooklmEnabled": NOTEBOOKLM_AVAILABLE,
                    "vaultWriteBackRequired": True,
                    "sessionSummaryRequired": True,
                    "prompt": build_project_launch_prompt(project, related_chats, related_workflows),
                },
            }
        )

    return {
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "vaultRoot": str(vault_root),
            "version": "1.0-project-registry",
        },
        "projects": registry_items,
    }


def build_weekly_project_brief(projects: list[dict[str, Any]], generated_at: str) -> str:
    today = parse_date(generated_at[:10]) or date.today()
    recent: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []

    for project in projects:
        if project.get("status") == "active":
            active.append(project)
        updated_at = parse_date(project.get("lastUpdated"))
        if updated_at and (today - updated_at).days <= 7:
            recent.append(project)
        if project.get("status") == "active" and not project.get("relatedChatIds") and not project.get("relatedWorkflowIds"):
            stale.append(project)

    recent.sort(key=lambda item: item.get("lastUpdated", ""), reverse=True)
    active.sort(key=lambda item: item.get("progress", 0), reverse=True)

    lines = [
        "# Weekly Project Brief",
        "",
        f"- Сформировано: **{generated_at}**",
        f"- Активных проектов: **{len(active)}**",
        f"- Обновлялись за 7 дней: **{len(recent)}**",
        "",
        "## Проекты с недавними изменениями",
    ]
    if recent:
        for project in recent[:10]:
            lines.append(
                f"- **{project['title']}** — {project.get('status', 'research')}, updated `{project.get('lastUpdated', '')}`, next: {next_project_step(project)}"
            )
    else:
        lines.append("- За последние 7 дней обновления не зафиксированы.")

    lines.extend(["", "## Активный фокус"])
    for project in active[:8]:
        lines.append(
            f"- **{project['title']}** — progress {project.get('progress', 0)}%, chats {project.get('relatedChatsCount', 0)}, workflows {project.get('relatedWorkflowsCount', 0)}"
        )

    lines.extend(["", "## Риски пустого контекста"])
    if stale:
        for project in stale[:8]:
            lines.append(f"- **{project['title']}** — активен, но без привязанных чатов и workflows.")
    else:
        lines.append("- Явно пустых активных контуров не найдено.")

    lines.extend(["", "## Следующие продуктовые шаги"])
    lines.extend(
        [
            "- Довести project registry до единой канонической схемы для dashboard, vault, chats и workflows.",
            "- Дозаполнить связанные чаты и workflows для активных проектов с пустым контекстом.",
            "- Поддерживать `project mode` как основной способ запуска агентных сценариев.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def load_system_profile(workspace_root: Path) -> dict[str, Any]:
    profile_path = workspace_root / DEFAULT_PROFILE_CONFIG
    loaded = read_json(profile_path, {})
    if not isinstance(loaded, dict):
        loaded = {}
    profile = merge_dicts(DEFAULT_SYSTEM_PROFILE, loaded)
    translations = dict(DEFAULT_PROJECT_TITLE_TRANSLATIONS)
    for source, target in (profile.get("projectTitleTranslations") or {}).items():
        if isinstance(source, str) and isinstance(target, str) and source.strip() and target.strip():
            translations[source.strip().casefold()] = target.strip()
    profile["projectTitleTranslations"] = translations
    return profile


def localize_project_title(title: str, translation_map: dict[str, str]) -> tuple[str, str]:
    raw = str(title).strip()
    if not raw:
        return "", ""
    if contains_cyrillic(raw):
        return raw, ""

    exact = translation_map.get(raw.casefold())
    if exact:
        return exact, raw

    normalized = raw.replace("_", " ").replace("-", " ")
    tokens = re.findall(r"[A-Za-z]+|\d+", normalized)
    translated_tokens: list[str] = []
    translated_count = 0
    for token in tokens:
        translated = PROJECT_TITLE_TOKEN_TRANSLATIONS.get(token.lower())
        if translated:
            translated_tokens.append(translated)
            translated_count += 1
        else:
            translated_tokens.append(token)
    if tokens and translated_count >= max(1, len(tokens) // 2):
        candidate = re.sub(r"\s+", " ", " ".join(translated_tokens)).strip()
        if candidate and candidate.casefold() != raw.casefold():
            return candidate[:1].upper() + candidate[1:], raw
    return raw, ""


def register_project_lookup(mapping: dict[str, str], project_id: str, *values: str) -> None:
    for value in values:
        key = str(value or "").strip().casefold()
        if key:
            mapping[key] = project_id


def list_unique(items: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def ensure_priority_projects(manual_projects: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
    result = [dict(project) for project in manual_projects]
    known_titles: set[str] = set()
    for project in result:
        for key in ("title", "originalTitle", "sourceTitle"):
            value = str(project.get(key, "")).strip().casefold()
            if value:
                known_titles.add(value)

    for project in profile.get("priorityProjects", []):
        if not isinstance(project, dict):
            continue
        title = str(project.get("title", "")).strip()
        source_title = str(project.get("sourceTitle") or project.get("originalTitle") or title).strip()
        if not title:
            continue
        if title.casefold() in known_titles or source_title.casefold() in known_titles:
            continue

        prepared = dict(project)
        prepared.setdefault("topic", "manual")
        prepared.setdefault("tags", [])
        prepared["tags"] = list(dict.fromkeys([*(prepared.get("tags") or []), "manual", "priority-system"]))
        prepared.setdefault("lastUpdated", date.today().isoformat())
        prepared.setdefault("sourceTitle", source_title)
        prepared.setdefault("originalTitle", "")
        result.append(prepared)

        for key in ("title", "originalTitle", "sourceTitle"):
            value = str(prepared.get(key, "")).strip().casefold()
            if value:
                known_titles.add(value)

    return result


def pick_latest(patterns: list[Path]) -> Path:
    existing = [p for p in patterns if p.exists()]
    if not existing:
        raise FileNotFoundError("Could not resolve required input file")
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return existing[0]


def resolve_sources(workspace_root: Path, args: argparse.Namespace) -> SourceBundle:
    docs_local = workspace_root / "docs"
    data_local = workspace_root / "data"
    base_projects_json = workspace_root / DEFAULT_MANUAL_BASE
    out_projects_json = workspace_root / DEFAULT_PROJECTS_OUT

    organization_candidates = []
    organization_candidates.extend(sorted(docs_local.glob("organization_audit_*.csv")))
    organization_candidates.extend(sorted(DEFAULT_ARCHIVE_REPORTS.glob("organization_audit_*.csv")))
    if args.organization_audit:
        organization_candidates.insert(0, Path(args.organization_audit))

    return SourceBundle(
        projects_index=pick_latest(
            [Path(args.projects_index)] if args.projects_index else [DEFAULT_ARCHIVE_DOCS / "projects_index.csv"]
        ),
        workflows_index=pick_latest(
            [Path(args.workflows_index)] if args.workflows_index else [DEFAULT_ARCHIVE_DOCS / "workflows_index.csv"]
        ),
        chats_index=pick_latest(
            [Path(args.chats_index)] if args.chats_index else [DEFAULT_ARCHIVE_DOCS / "antigravity_chat_index.csv"]
        ),
        organization_audit=pick_latest(organization_candidates),
        base_projects_json=Path(args.base_projects_json) if args.base_projects_json else base_projects_json,
        obsidian_root=Path(args.obsidian_root) if args.obsidian_root else DEFAULT_OBSIDIAN_ROOT,
        out_dashboard_json=Path(args.out_dashboard_json)
        if args.out_dashboard_json
        else data_local / "dashboard_data.json",
        out_mindmap_json=Path(args.out_mindmap_json) if args.out_mindmap_json else data_local / "mindmap.json",
        out_projects_json=Path(args.out_projects_json) if args.out_projects_json else out_projects_json,
        out_project_registry_json=data_local / "project_registry.json",
    )


def map_status(migration_status: str | None, preferred: str | None) -> str:
    s = (preferred or "").strip().lower()
    if s in STATUS_RU:
        return s

    m = (migration_status or "").strip().lower()
    if "missing_source_and_destination" in m:
        return "backlog"
    if "recovered_fragments_only" in m:
        return "research"
    if "destination_missing" in m:
        return "research"
    if "migrated" in m:
        return "active"
    return "research"


def map_progress(status: str, source_exists: bool, destination_exists: bool, current: int | None = None) -> int:
    base = {
        "active": 65,
        "paused": 45,
        "research": 35,
        "backlog": 15,
        "done": 100,
    }.get(status, 30)
    if source_exists and destination_exists:
        base = max(base, 80)
    if not source_exists and not destination_exists:
        base = min(base, 20)
    if current is not None:
        base = max(base, current)
    return max(0, min(100, int(base)))


def category_from_topic(topic: str | None, fallback: str = "Прочее") -> str:
    if not topic:
        return fallback
    return TOPIC_LABELS.get(topic.strip().lower(), fallback)


def latest_date(values: list[str]) -> str:
    parsed = [parse_date(v) for v in values]
    parsed = [d for d in parsed if d is not None]
    if not parsed:
        return date.today().isoformat()
    return max(parsed).isoformat()


def summarize_text(value: str | None, max_len: int = 240) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def tokenize_text(value: str | None) -> list[str]:
    if not value:
        return []
    return [token.casefold() for token in re.findall(r"[A-Za-zА-Яа-яЁё]{3,}", str(value))]


def priority_score(value: str | None) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(str(value or "").strip().lower(), 2)


def infer_theme(text: str) -> str:
    lowered = text.casefold()
    if re.search(r"(семья|дети|дом|подар|family|home)", lowered):
        return "family"
    if re.search(r"(образован|гимназ|школ|грант|education|teacher|school)", lowered):
        return "education"
    if re.search(r"(rag|knowledge|obsidian|база знаний|second brain|mindmap|карта|дашборд|поиск|monitor)", lowered):
        return "knowledge"
    if re.search(r"(agent|агент|skill|workflow|автомат|router|orchestrat|parser|парсер|telegram бот|cli|ide)", lowered):
        return "agents"
    if re.search(r"(video|видео|youtube|remotion|tts|stt|озвучк|контент|media)", lowered):
        return "media"
    if re.search(r"(product|продукт|сервис|platform|платформ|meeting|app|приложен|landing|лендинг|ассистент)", lowered):
        return "product"
    if re.search(r"(research|исследован|анализ|radar|atlas)", lowered):
        return "research"
    return "general"


def infer_life_area(
    text: str,
    profile: dict[str, Any],
    matched_project: dict[str, Any] | None = None,
    theme: str | None = None,
) -> tuple[str, str]:
    lowered = text.casefold()
    profile_areas = {
        str(item.get("id", "")).strip(): str(item.get("label", "")).strip()
        for item in profile.get("lifeAreas", [])
        if isinstance(item, dict) and item.get("id")
    }
    area_labels = {**LIFE_AREA_FALLBACK_LABELS, **profile_areas}

    if re.search(r"(семья|дети|дом|подар|family|home)", lowered):
        return "семья", area_labels.get("семья", "Семья")

    if matched_project:
        category = str(matched_project.get("category", "")).casefold()
        topic = str(matched_project.get("topic", "")).casefold()
        if "сем" in category:
            return "семья", area_labels.get("семья", "Семья")
        if "лич" in category:
            return "я", area_labels.get("я", "Я")
        if topic in {"manual", "antigravity"} and not re.search(r"(ai|агент|образован|грант|инфра|продукт|работ)", category):
            return "я", area_labels.get("я", "Я")
        return "работа", area_labels.get("работа", "Работа")

    if theme in {"education", "agents", "product", "media", "research"}:
        return "работа", area_labels.get("работа", "Работа")
    if theme == "knowledge":
        return "я", area_labels.get("я", "Я")
    return "я", area_labels.get("я", "Я")


def find_related_project(projects: list[dict[str, Any]], related_value: str, text: str) -> dict[str, Any] | None:
    related_key = str(related_value or "").strip().casefold()
    if related_key:
        for project in projects:
            keys = {
                str(project.get("id", "")).strip().casefold(),
                str(project.get("title", "")).strip().casefold(),
                str(project.get("originalTitle", "")).strip().casefold(),
                str(project.get("sourceTitle", "")).strip().casefold(),
            }
            if related_key in keys:
                return project

    lowered = text.casefold()
    for project in projects:
        project_title = str(project.get("title", "")).strip()
        original_title = str(project.get("originalTitle", "")).strip()
        if project_title and project_title.casefold() in lowered:
            return project
        if original_title and original_title.casefold() in lowered:
            return project
    return None


def build_idea_router(
    profile: dict[str, Any],
    projects: list[dict[str, Any]],
    ideas: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    cluster_meta: dict[str, dict[str, Any]] = {}

    for idea in ideas:
        title = str(idea.get("title", "")).strip() or "Идея"
        description = str(idea.get("description") or idea.get("comment") or "").strip()
        priority = str(idea.get("priority") or "medium").strip().lower()
        related_project_raw = str(idea.get("relatedProject", "")).strip()
        text = " ".join([title, description, " ".join(idea.get("tags", []) or []), related_project_raw]).strip()
        tokens = tokenize_text(text)
        matched_project = find_related_project(projects, related_project_raw, text)
        theme = infer_theme(text)
        life_area, life_area_label = infer_life_area(text, profile, matched_project=matched_project, theme=theme)

        lowered = text.casefold()
        skill_signal = bool(
            re.search(r"(skill|навык|workflow|агент|автомат|router|triage|parser|парсер|pipeline|sync|монитор)", lowered)
        )
        project_signal = bool(
            re.search(r"(проект|система|контур|дашборд|карта|база|factory|atlas|radar|платформ|сервис|ассистент|двойник)", lowered)
        )
        archive_signal = priority == "low" and len(tokens) <= 8 and not matched_project

        route = "reference_note"
        reason = "Материал лучше сохранить как компактную заметку с дальнейшей привязкой по мере накопления контекста."
        next_step = "Сделать reference-note: суть, теги, применение, связь с текущими темами."
        routing_score = 55 + priority_score(priority) * 8

        if matched_project:
            route = "project_update"
            reason = f"Есть явная привязка к проекту «{matched_project['title']}»."
            next_step = "Обновить карточку проекта: добавить суть идеи, теги и ближайший эксперимент."
            routing_score = 92 + priority_score(priority)
        elif skill_signal and theme in {"agents", "knowledge"}:
            route = "skill_candidate"
            reason = "В идее виден повторяемый агентный или инфраструктурный паттерн, который стоит оформить как skill."
            next_step = "Описать входы, выходы, ограничения и шаблон использования в CLI/IDE."
            routing_score = 80 + priority_score(priority)
        elif project_signal or priority in {"high", "medium"}:
            route = "project_hypothesis"
            reason = "Сигнал достаточно сильный, чтобы оформить отдельную гипотезу с ближайшим экспериментом."
            next_step = "Создать короткую проектную гипотезу: цель, ценность, первый тест, связи."
            routing_score = 72 + priority_score(priority) * 3
        elif archive_signal:
            route = "archive"
            reason = "Пока нет ни связи, ни достаточного сигнала для отдельной сущности."
            next_step = "Оставить минимальный индекс и не поднимать идею в активный контур."
            routing_score = 28

        if matched_project:
            cluster_id = f"project-{matched_project['id']}"
            cluster_title = f"Проект: {matched_project['title']}"
        else:
            cluster_id = f"{life_area}-{theme}-{route}"
            cluster_title = f"{THEME_LABELS.get(theme, 'Общий контур')} / {life_area_label}"

        enriched_idea = {
            **idea,
            "priority": priority or "medium",
            "theme": theme,
            "themeLabel": THEME_LABELS.get(theme, "Общий контур"),
            "lifeArea": life_area,
            "lifeAreaLabel": life_area_label,
            "route": route,
            "routeLabel": ROUTE_LABELS.get(route, route),
            "routingReason": reason,
            "routingNextStep": next_step,
            "routingScore": routing_score,
            "relatedProject": matched_project["title"] if matched_project else related_project_raw,
            "relatedProjectId": matched_project["id"] if matched_project else "",
            "clusterId": cluster_id,
            "clusterTitle": cluster_title,
        }
        enriched.append(enriched_idea)

        cluster = cluster_meta.setdefault(
            cluster_id,
            {
                "id": cluster_id,
                "title": cluster_title,
                "theme": theme,
                "themeLabel": THEME_LABELS.get(theme, "Общий контур"),
                "lifeArea": life_area,
                "lifeAreaLabel": life_area_label,
                "relatedProject": matched_project["title"] if matched_project else "",
                "ideaIds": [],
                "ideaTitles": [],
                "routes": Counter(),
                "tags": Counter(),
                "maxScore": 0,
            },
        )
        cluster["ideaIds"].append(enriched_idea["id"])
        cluster["ideaTitles"].append(title)
        cluster["routes"][route] += 1
        cluster["maxScore"] = max(cluster["maxScore"], routing_score)
        for tag in enriched_idea.get("tags", []) or []:
            if str(tag).strip():
                cluster["tags"][str(tag).strip()] += 1

    enriched.sort(
        key=lambda item: (
            -int(item.get("routingScore", 0)),
            -priority_score(item.get("priority")),
            str(item.get("addedDate", "")),
            str(item.get("title", "")).casefold(),
        )
    )

    route_counts = Counter(item.get("route", "reference_note") for item in enriched)
    clusters: list[dict[str, Any]] = []
    for cluster in cluster_meta.values():
        route_bias = cluster["routes"].most_common(1)[0][0] if cluster["routes"] else "reference_note"
        clusters.append(
            {
                "id": cluster["id"],
                "title": cluster["title"],
                "theme": cluster["theme"],
                "themeLabel": cluster["themeLabel"],
                "lifeArea": cluster["lifeArea"],
                "lifeAreaLabel": cluster["lifeAreaLabel"],
                "relatedProject": cluster["relatedProject"],
                "ideaCount": len(cluster["ideaIds"]),
                "ideaIds": cluster["ideaIds"],
                "ideaTitles": cluster["ideaTitles"][:5],
                "routeBias": route_bias,
                "routeBiasLabel": ROUTE_LABELS.get(route_bias, route_bias),
                "topTags": [tag for tag, _ in cluster["tags"].most_common(5)],
                "summary": summarize_text(" · ".join(cluster["ideaTitles"][:3]), 180),
                "nextStep": next(
                    (
                        item.get("routingNextStep", "")
                        for item in enriched
                        if item.get("clusterId") == cluster["id"] and item.get("routingNextStep")
                    ),
                    "",
                ),
                "score": cluster["maxScore"],
            }
        )
    clusters.sort(key=lambda item: (-item["ideaCount"], -item["score"], item["title"].casefold()))

    queue = [
        {
            "ideaId": item["id"],
            "title": item["title"],
            "route": item["route"],
            "routeLabel": item["routeLabel"],
            "reason": item["routingReason"],
            "nextStep": item["routingNextStep"],
            "relatedProject": item.get("relatedProject", ""),
            "lifeAreaLabel": item.get("lifeAreaLabel", ""),
            "themeLabel": item.get("themeLabel", ""),
            "priority": item.get("priority", "medium"),
            "score": item.get("routingScore", 0),
        }
        for item in enriched[:12]
    ]

    top_clusters = [
        f"{cluster['title']} — {cluster['ideaCount']} идей, базовый исход: {cluster['routeBiasLabel']}"
        for cluster in clusters[:5]
    ]

    return enriched, {
        "summary": {
            "totalIdeas": len(enriched),
            "clusterCount": len(clusters),
            "routedToProject": route_counts.get("project_update", 0),
            "skillCandidates": route_counts.get("skill_candidate", 0),
            "projectHypotheses": route_counts.get("project_hypothesis", 0),
            "referenceNotes": route_counts.get("reference_note", 0),
            "archiveItems": route_counts.get("archive", 0),
        },
        "queue": queue,
        "clusters": clusters,
        "recommendations": [
            "Сначала разбирать идеи с явной привязкой к проектам: они быстрее всего превращаются в действие.",
            "Skill-кандидаты поднимать только там, где виден повторяемый паттерн, а не разовый интерес.",
            "Новые проектные гипотезы оформлять через один ближайший эксперимент, а не через длинный backlog.",
            *top_clusters,
        ][:8],
    }


def text_signature(text: str | None) -> set[str]:
    tokens = tokenize_text(text or "")
    stop = {
        "проект",
        "проекты",
        "workspace",
        "dashboard",
        "система",
        "сервис",
        "новый",
        "новая",
        "идея",
        "для",
        "как",
        "или",
    }
    return {token for token in tokens if token not in stop}


def project_alias_strings(project: dict[str, Any]) -> list[str]:
    values = [
        str(project.get("id", "")).replace("-", " "),
        str(project.get("title", "")),
        str(project.get("originalTitle", "")),
        str(project.get("sourceTitle", "")),
    ]
    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = re.sub(r"\s+", " ", value).strip()
        key = clean.casefold()
        if not clean or key in seen:
            continue
        seen.add(key)
        aliases.append(clean)
    return aliases


def read_text_snippet(path: Path, max_chars: int = 4000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[:max_chars]


def collect_chat_evidence_text(chat: dict[str, Any]) -> str:
    parts = [
        str(chat.get("title", "")).strip(),
        str(chat.get("summary", "")).strip(),
        str(chat.get("theme", "")).strip(),
    ]
    for key in ("conversationPath", "brainPath"):
        raw = str(chat.get(key, "")).strip()
        if raw and Path(raw).exists() and Path(raw).is_file() and Path(raw).suffix.lower() == ".md":
            snippet = read_text_snippet(Path(raw), max_chars=2500)
            if snippet:
                parts.append(snippet)
    for raw in (chat.get("referencedPaths", []) or [])[:3]:
        path = Path(str(raw))
        if not path.exists() or not path.is_file() or path.suffix.lower() != ".md":
            continue
        snippet = read_text_snippet(path, max_chars=2500)
        if snippet:
            parts.append(snippet)
    return "\n".join(part for part in parts if part).strip()


def infer_projects_from_hint_rules(text: str, available_project_ids: set[str]) -> set[str]:
    lowered = text.casefold()
    matched: set[str] = set()
    for pattern, project_ids in PROJECT_HINT_RULES:
        if not re.search(pattern, lowered):
            continue
        for project_id in project_ids:
            if project_id in available_project_ids:
                matched.add(project_id)
    return matched


def score_chat_project_link(
    chat: dict[str, Any],
    project: dict[str, Any],
    project_alias_paths: dict[str, list[str]],
    evidence_text: str,
    hinted_projects: set[str],
) -> float:
    score = 0.0
    lowered = evidence_text.casefold()

    for alias in project_alias_strings(project):
        alias_lower = alias.casefold()
        if len(alias_lower) >= 4 and alias_lower in lowered:
            score += 6.0 if alias == project.get("title") else 4.5
            break

    chat_signature = text_signature(evidence_text)
    project_signature = text_signature(
        " ".join(
            [
                str(project.get("title", "")),
                str(project.get("originalTitle", "")),
                str(project.get("sourceTitle", "")),
                str(project.get("description", "")),
                " ".join(project.get("tags", []) or []),
            ]
        )
    )
    score += jaccard_similarity(chat_signature, project_signature) * 5.0

    project_id = str(project.get("id", ""))
    if project_id in hinted_projects:
        score += 6.0

    path_tokens = [
        str(chat.get("conversationPath", "")).strip(),
        str(chat.get("brainPath", "")).strip(),
        *(str(item).strip() for item in (chat.get("referencedPaths", []) or [])),
        *(str(item).strip() for item in (chat.get("workflowPaths", []) or [])),
    ]
    aliases = project_alias_paths.get(project_id, [])
    if any(path_related(token, alias) for token in path_tokens for alias in aliases):
        score += 8.0

    project_topic = str(project.get("topic", "")).strip().casefold()
    if project_topic and project_topic in lowered:
        score += 1.5

    return score


def autolink_chat_project_ids(
    chats: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    project_alias_paths: dict[str, list[str]],
) -> int:
    project_ids = {str(project.get("id", "")) for project in projects}
    linked_count = 0

    for chat in chats:
        if chat.get("relatedProjectIds"):
            continue
        evidence_text = collect_chat_evidence_text(chat)
        if not evidence_text:
            continue

        hinted_projects = infer_projects_from_hint_rules(evidence_text, project_ids)
        scored: list[tuple[float, str]] = []
        for project in projects:
            project_id = str(project.get("id", ""))
            score = score_chat_project_link(chat, project, project_alias_paths, evidence_text, hinted_projects)
            if score > 0:
                scored.append((score, project_id))

        if not scored:
            continue

        scored.sort(reverse=True)
        best_score = scored[0][0]
        selected = [
            project_id
            for score, project_id in scored[:6]
            if score >= 5.5 and (score >= best_score - 1.0 or (project_id in hinted_projects and score >= 5.0))
        ][:3]
        if not selected:
            continue

        chat["relatedProjectIds"] = sorted(set(selected))
        linked_count += 1

    return linked_count


def sanitize_related_project_ids(
    projects: list[dict[str, Any]],
    chats: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
) -> None:
    known_project_ids = {str(project.get("id", "")) for project in projects}
    for chat in chats:
        chat["relatedProjectIds"] = [pid for pid in chat.get("relatedProjectIds", []) if pid in known_project_ids]
    for workflow in workflows:
        workflow["relatedProjectIds"] = [pid for pid in workflow.get("relatedProjectIds", []) if pid in known_project_ids]


def rebuild_project_relationships(
    projects: list[dict[str, Any]],
    chats: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
) -> None:
    project_to_chat_ids: dict[str, set[str]] = defaultdict(set)
    project_to_workflow_ids: dict[str, set[str]] = defaultdict(set)

    for chat in chats:
        for pid in chat.get("relatedProjectIds", []) or []:
            project_to_chat_ids[pid].add(chat["id"])

    for workflow in workflows:
        for pid in workflow.get("relatedProjectIds", []) or []:
            project_to_workflow_ids[pid].add(workflow["id"])

    for project in projects:
        pid = project["id"]
        related_chat_ids = sorted(set(project.get("relatedChatIds", [])) | project_to_chat_ids.get(pid, set()))
        related_workflow_ids = sorted(set(project.get("relatedWorkflowIds", [])) | project_to_workflow_ids.get(pid, set()))
        project["relatedChatIds"] = related_chat_ids
        project["relatedChatsCount"] = len(related_chat_ids)
        project["relatedWorkflowIds"] = related_workflow_ids
        project["relatedWorkflowsCount"] = len(related_workflow_ids)


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def project_quality_score(project: dict[str, Any]) -> int:
    score = 0
    score += int(project.get("progress", 0))
    score += 30 if project.get("status") == "active" else 0
    score += 8 * len(project.get("relatedChatIds", []) or [])
    score += 6 * len(project.get("relatedWorkflowIds", []) or [])
    score += 15 if project.get("destinationExists") else 0
    score += 5 if project.get("sourceExists") else 0
    if str(project.get("migrationStatus", "")).strip() in {"missing_source_and_destination", "recovered_fragments_only"}:
        score -= 30
    score += min(18, len(str(project.get("description", "")).strip()) // 40)
    return score


def chat_quality_score(chat: dict[str, Any]) -> int:
    score = 0
    if str(chat.get("recoveryStatus", "")).casefold() == "recovered":
        score += 30
    score += min(30, len(str(chat.get("summary", "")).strip()) // 8)
    score += 6 * len(chat.get("relatedProjectIds", []) or [])
    score += 2 * len(chat.get("referencedPaths", []) or [])
    score += 2 * len(chat.get("workflowPaths", []) or [])
    return score


def project_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    title_a = text_signature(" ".join([str(a.get("title", "")), str(a.get("originalTitle", "")), str(a.get("sourceTitle", ""))]))
    title_b = text_signature(" ".join([str(b.get("title", "")), str(b.get("originalTitle", "")), str(b.get("sourceTitle", ""))]))
    tag_a = text_signature(" ".join(a.get("tags", []) or []))
    tag_b = text_signature(" ".join(b.get("tags", []) or []))
    topic_bonus = 0.2 if str(a.get("topic", "")).strip().casefold() == str(b.get("topic", "")).strip().casefold() else 0.0
    category_bonus = 0.1 if str(a.get("category", "")).strip().casefold() == str(b.get("category", "")).strip().casefold() else 0.0
    group_bonus = 0.0
    group_a, _ = classify_project_group(a)
    group_b, _ = classify_project_group(b)
    if group_a == group_b:
        group_bonus = 0.15
    title_score = jaccard_similarity(title_a, title_b)
    tag_score = jaccard_similarity(tag_a, tag_b)
    return min(1.0, 0.65 * title_score + 0.25 * tag_score + topic_bonus + category_bonus + group_bonus)


def chat_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    title_a = text_signature(str(a.get("title", "")))
    title_b = text_signature(str(b.get("title", "")))
    summary_a = text_signature(str(a.get("summary", "")))
    summary_b = text_signature(str(b.get("summary", "")))
    theme_bonus = 0.2 if str(a.get("theme", "")).strip().casefold() == str(b.get("theme", "")).strip().casefold() else 0.0
    return min(1.0, 0.6 * jaccard_similarity(title_a, title_b) + 0.25 * jaccard_similarity(summary_a, summary_b) + theme_bonus)


def classify_project_group(project: dict[str, Any]) -> tuple[str, str]:
    text = " ".join(
        [
            str(project.get("title", "")),
            str(project.get("originalTitle", "")),
            str(project.get("description", "")),
            str(project.get("topic", "")),
            " ".join(project.get("tags", []) or []),
        ]
    ).casefold()

    rules = [
        (
            "work-projects",
            "Рабочие проекты (Гимназия/Бизнес)",
            r"(гимназ|школ|davydov|грант|grant|кoра|кора|business|бизнес|компан|landing|strategy|панел|meeting|совещан)",
        ),
        (
            "news-aggregators",
            "Агрегаторы новостей и мониторинг",
            r"(aggregat|агрегат|новост|монитор|telegram|tg|youtube|ютуб|parser|парсер|scrap|scrape|crawl|канал|источник)",
        ),
        (
            "idea-generators",
            "Генераторы идей и визуализация",
            r"(иде[яй]|idea|brainstorm|майнд|mindmap|hypothesis|гипотез|визуал|insight|radar|roadmap)",
        ),
        (
            "ai-system-growth",
            "Развитие ИИ-системы (ядро/база знаний)",
            r"(second brain|второй мозг|knowledge|база знаний|obsidian|dashboard|дашборд|library|библиотек|script|скрипт|core|workspace)",
        ),
        (
            "ai-agents",
            "ИИ-агенты и автоматизация",
            r"(agent|агент|subagent|workflow|automation|автомат|skill|навык|router|n8n|cli|ide|copilot|mcp)",
        ),
    ]

    for group_id, group_title, pattern in rules:
        if re.search(pattern, text):
            return group_id, group_title

    return "ai-system-growth", "Развитие ИИ-системы (ядро/база знаний)"


def build_project_groups(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for project in projects:
        gid, gtitle = classify_project_group(project)
        project["groupId"] = gid
        project["groupTitle"] = gtitle
        group = groups.setdefault(
            gid,
            {
                "id": gid,
                "title": gtitle,
                "projectIds": [],
                "projectTitles": [],
                "topics": Counter(),
                "statusCounts": Counter(),
            },
        )
        group["projectIds"].append(project["id"])
        group["projectTitles"].append(project["title"])
        group["topics"][str(project.get("topic", "manual"))] += 1
        group["statusCounts"][str(project.get("status", "research"))] += 1

    payload: list[dict[str, Any]] = []
    for group in groups.values():
        payload.append(
            {
                "id": group["id"],
                "title": group["title"],
                "projectCount": len(group["projectIds"]),
                "projectIds": group["projectIds"],
                "projectTitles": group["projectTitles"][:8],
                "topTopics": [topic for topic, _ in group["topics"].most_common(3)],
                "activeProjects": int(group["statusCounts"].get("active", 0)),
                "researchProjects": int(group["statusCounts"].get("research", 0)),
            }
        )
    group_priority = {
        "news-aggregators": 1,
        "idea-generators": 2,
        "ai-system-growth": 3,
        "ai-agents": 4,
        "work-projects": 5,
    }
    payload.sort(key=lambda item: (group_priority.get(item["id"], 99), -item["projectCount"], item["title"].casefold()))
    return payload


def archive_and_consolidate_sources(
    projects: list[dict[str, Any]],
    chats: list[dict[str, Any]],
    workflows: list[dict[str, Any]],
    ideas: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    archives: list[dict[str, Any]] = []

    # Step 1. Archive chats that are unrecovered or effectively empty.
    kept_chats: list[dict[str, Any]] = []
    chat_replacement: dict[str, str] = {}
    for chat in chats:
        summary = str(chat.get("summary", "")).strip()
        unrecovered = str(chat.get("recoveryStatus", "")).strip().casefold() == "unrecovered"
        meaningless = len(summary) < 24 and not chat.get("relatedProjectIds") and not chat.get("referencedPaths")
        if unrecovered or meaningless:
            chat_title = str(chat.get("title", "")).strip() or "Untitled chat"
            if chat_title.casefold() == "untitled chat":
                chat_title = f"Untitled chat ({str(chat.get('id', ''))[:8]})"
            archives.append(
                {
                    "kind": "chat",
                    "id": chat.get("id", ""),
                    "title": chat_title,
                    "reason": "unrecovered_or_meaningless",
                    "recoveryStatus": chat.get("recoveryStatus", ""),
                }
            )
            continue
        kept_chats.append(chat)

    # Step 2. Consolidate similar chats.
    chat_removed: set[str] = set()
    for i in range(len(kept_chats)):
        a = kept_chats[i]
        if a["id"] in chat_removed:
            continue
        for j in range(i + 1, len(kept_chats)):
            b = kept_chats[j]
            if b["id"] in chat_removed:
                continue
            same_path = (
                normalize_path(a.get("conversationPath")) == normalize_path(b.get("conversationPath"))
                and normalize_path(a.get("conversationPath"))
            ) or (
                normalize_path(a.get("brainPath")) == normalize_path(b.get("brainPath"))
                and normalize_path(a.get("brainPath"))
            )
            if not same_path and chat_similarity(a, b) < 0.9:
                continue
            primary, secondary = (a, b) if chat_quality_score(a) >= chat_quality_score(b) else (b, a)
            primary["relatedProjectIds"] = sorted(
                set(primary.get("relatedProjectIds", []) or []) | set(secondary.get("relatedProjectIds", []) or [])
            )
            primary["referencedPaths"] = list_unique([*(primary.get("referencedPaths", []) or []), *(secondary.get("referencedPaths", []) or [])])[:12]
            primary["workflowPaths"] = list_unique([*(primary.get("workflowPaths", []) or []), *(secondary.get("workflowPaths", []) or [])])[:8]
            primary["summary"] = summarize_text(
                " ".join([str(primary.get("summary", "")).strip(), str(secondary.get("summary", "")).strip()]).strip(),
                260,
            )
            chat_replacement[secondary["id"]] = primary["id"]
            chat_removed.add(secondary["id"])
            archives.append(
                {
                    "kind": "chat",
                    "id": secondary.get("id", ""),
                    "title": secondary.get("title", ""),
                    "reason": "merged_into_chat",
                    "mergedInto": primary.get("id", ""),
                }
            )

    chats = [chat for chat in kept_chats if chat["id"] not in chat_removed]

    # Step 3. Archive incomplete/weak projects.
    kept_projects: list[dict[str, Any]] = []
    project_replacement: dict[str, str] = {}
    for project in projects:
        migration_status = str(project.get("migrationStatus", "")).strip()
        non_recovered = migration_status in {"missing_source_and_destination", "recovered_fragments_only"}
        weak_project = (
            int(project.get("progress", 0)) < 35
            and not project.get("relatedChatIds")
            and not project.get("relatedWorkflowIds")
        )
        if non_recovered or (weak_project and migration_status == "autodiscovered"):
            archives.append(
                {
                    "kind": "project",
                    "id": project.get("id", ""),
                    "title": project.get("title", ""),
                    "reason": "non_recovered_or_weak",
                    "migrationStatus": migration_status,
                }
            )
            continue
        kept_projects.append(project)

    # Step 4. Consolidate similar projects.
    project_removed: set[str] = set()
    for i in range(len(kept_projects)):
        a = kept_projects[i]
        if a["id"] in project_removed:
            continue
        for j in range(i + 1, len(kept_projects)):
            b = kept_projects[j]
            if b["id"] in project_removed:
                continue
            if project_similarity(a, b) < 0.7:
                continue
            primary, secondary = (a, b) if project_quality_score(a) >= project_quality_score(b) else (b, a)
            primary["tags"] = list_unique([*(primary.get("tags", []) or []), *(secondary.get("tags", []) or [])])
            primary["relatedChatIds"] = sorted(
                set(primary.get("relatedChatIds", []) or []) | set(secondary.get("relatedChatIds", []) or [])
            )
            primary["relatedWorkflowIds"] = sorted(
                set(primary.get("relatedWorkflowIds", []) or []) | set(secondary.get("relatedWorkflowIds", []) or [])
            )
            primary["relatedChatsCount"] = len(primary["relatedChatIds"])
            primary["relatedWorkflowsCount"] = len(primary["relatedWorkflowIds"])
            primary["progress"] = max(int(primary.get("progress", 0)), int(secondary.get("progress", 0)))
            extra = summarize_text(secondary.get("description"), 160)
            if extra and extra.casefold() not in str(primary.get("description", "")).casefold():
                primary["description"] = summarize_text(
                    f"{str(primary.get('description', '')).strip()} Интегрировано: {extra}".strip(),
                    320,
                )
            primary.setdefault("mergedFrom", [])
            primary["mergedFrom"].append(
                {
                    "id": secondary.get("id", ""),
                    "title": secondary.get("title", ""),
                    "summary": extra,
                }
            )
            note_suffix = f" | Интегрировано из: {secondary.get('title', '')}"
            primary["notes"] = f"{str(primary.get('notes', '')).strip()}{note_suffix}".strip()
            project_replacement[secondary["id"]] = primary["id"]
            project_removed.add(secondary["id"])
            archives.append(
                {
                    "kind": "project",
                    "id": secondary.get("id", ""),
                    "title": secondary.get("title", ""),
                    "reason": "merged_into_project",
                    "mergedInto": primary.get("id", ""),
                }
            )

    projects = [project for project in kept_projects if project["id"] not in project_removed]

    # Step 5. Remap references after consolidation.
    def remap_project_id(value: str) -> str:
        cursor = value
        while cursor in project_replacement:
            cursor = project_replacement[cursor]
        return cursor

    def remap_chat_id(value: str) -> str:
        cursor = value
        while cursor in chat_replacement:
            cursor = chat_replacement[cursor]
        return cursor

    for project in projects:
        mapped_chats = [remap_chat_id(cid) for cid in (project.get("relatedChatIds", []) or [])]
        mapped_workflows = list(project.get("relatedWorkflowIds", []) or [])
        project["relatedChatIds"] = sorted(set(mapped_chats))
        project["relatedChatsCount"] = len(project["relatedChatIds"])
        project["relatedWorkflowIds"] = sorted(set(mapped_workflows))
        project["relatedWorkflowsCount"] = len(project["relatedWorkflowIds"])

    for chat in chats:
        mapped = [remap_project_id(pid) for pid in (chat.get("relatedProjectIds", []) or [])]
        chat["relatedProjectIds"] = sorted(set(mapped))

    for workflow in workflows:
        mapped = [remap_project_id(pid) for pid in (workflow.get("relatedProjectIds", []) or [])]
        workflow["relatedProjectIds"] = sorted(set(mapped))
        mapped_chat_ids = [remap_chat_id(cid) for cid in (workflow.get("relatedChatIds", []) or [])]
        workflow["relatedChatIds"] = sorted(set(mapped_chat_ids))

    known_project_ids = {str(project.get("id", "")) for project in projects}
    for chat in chats:
        chat["relatedProjectIds"] = [pid for pid in chat.get("relatedProjectIds", []) if pid in known_project_ids]
    for workflow in workflows:
        workflow["relatedProjectIds"] = [pid for pid in workflow.get("relatedProjectIds", []) if pid in known_project_ids]

    for idea in ideas:
        related = str(idea.get("relatedProject", "")).strip()
        if not related:
            continue
        for project in projects:
            if related.casefold() in {
                str(project.get("id", "")).casefold(),
                str(project.get("title", "")).casefold(),
                str(project.get("originalTitle", "")).casefold(),
                str(project.get("sourceTitle", "")).casefold(),
            }:
                idea["relatedProject"] = project.get("title", related)
                break

    consolidation = {
        "summary": {
            "archivedProjects": sum(1 for item in archives if item.get("kind") == "project"),
            "archivedChats": sum(1 for item in archives if item.get("kind") == "chat"),
            "projectMerges": sum(1 for item in archives if item.get("reason") == "merged_into_project"),
            "chatMerges": sum(1 for item in archives if item.get("reason") == "merged_into_chat"),
        },
        "archives": archives,
    }

    return projects, chats, workflows, ideas, consolidation


def yaml_safe(value: str) -> str:
    return value.replace('"', "'")


def extract_title_summary_from_md(path: Path) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = ""
    summary = ""
    for ln in lines:
        if ln.startswith("#"):
            title = ln.lstrip("#").strip()
            break
    for ln in lines:
        if ln.startswith("#"):
            continue
        summary = ln
        break
    if not title:
        title = path.stem
    return title, summarize_text(summary, 220)


def extract_web_links(workspace_root: Path) -> dict[str, list[dict[str, str]]]:
    links: dict[str, list[dict[str, str]]] = {}

    gym_sources = [
        workspace_root / "gymnasium_site_v2" / "index.html",
        workspace_root / "gymnasium_site_v2_publish" / "index.html",
        workspace_root / "tmp_snapshot_extract" / "index.html",
    ]
    gym_url = ""
    for path in gym_sources:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        match = re.search(r"fallbackShareUrl\s*=\s*['\"]([^'\"]+)['\"]", text)
        if match:
            gym_url = match.group(1).strip()
            break
    if gym_url:
        links["gymnasium-landing"] = [
            {"label": "Сайт проекта", "url": gym_url},
        ]

    techno_url = ""
    techno_targets = [
        Path(r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\Грант для гимназии Давыдова\Инженерный грант\technostart_presentation.html"),
        workspace_root / "technostart_presentation.html",
        workspace_root / "technostart_fpg_final.html",
    ]
    for path in techno_targets:
        if path.exists():
            techno_url = path.resolve().as_uri()
            break

    techno_sources = [
        workspace_root / "gymnasium_site_v2" / "index.html",
        workspace_root / "gymnasium_site_v2_publish" / "index.html",
    ]
    if not techno_url:
        for path in techno_sources:
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            match = re.search(r'href="(http://127\\.0\\.0\\.1:8787/technostart_fpg_final\\.html)"', text)
            if match:
                techno_url = match.group(1).strip()
                break
    if techno_url:
        links["technostart"] = [
            {"label": "Веб-презентация", "url": techno_url},
        ]
        links["grant-presentation"] = [
            {"label": "Веб-презентация", "url": techno_url},
        ]

    return links


def should_replace_link(existing: list[dict[str, str]] | None, new_url: str) -> bool:
    if not existing:
        return True
    existing_url = str(existing[0].get("url", "")).strip()
    if not existing_url:
        return True
    if existing_url.startswith("file:") and new_url.startswith("http"):
        return True
    if "netlify.app" in existing_url and "netlify.app" not in new_url:
        return True
    return False


def html_candidates_from_path(raw: str) -> list[Path]:
    if not is_specific_path(raw):
        return []
    path = Path(raw)
    if path.exists() and path.is_file() and path.suffix.lower() in {".html", ".htm"}:
        return [path]
    if not path.exists() or not path.is_dir():
        return []
    preferred = [
        path / "index.html",
        path / "index.htm",
        path / "technostart_presentation.html",
        path / "technostart_fpg_final.html",
    ]
    candidates = [p for p in preferred if p.exists()]
    if candidates:
        return candidates
    extras = sorted(path.glob("*.html"))[:3]
    return extras


def extract_preferred_url(html_text: str) -> str:
    patterns = [
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
        r'fallbackShareUrl\s*=\s*["\']([^"\']+)["\']',
        r'currentShareUrl\s*=\s*["\']([^"\']+)["\']',
        r'data-site-url=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def attach_fallback_web_links(projects: list[dict[str, Any]], chats: list[dict[str, Any]]) -> None:
    project_paths: dict[str, list[str]] = defaultdict(list)
    for project in projects:
        pid = project.get("id", "")
        for key in ("destinationPath", "sourcePath"):
            raw = str(project.get(key, "")).strip()
            if is_specific_path(raw):
                project_paths[pid].append(raw)

    for chat in chats:
        related = chat.get("relatedProjectIds", []) or []
        for pid in related:
            for raw in (chat.get("referencedPaths", []) or []):
                if is_specific_path(raw):
                    project_paths[pid].append(raw)
            for raw in (chat.get("workflowPaths", []) or []):
                if is_specific_path(raw):
                    project_paths[pid].append(raw)

    for project in projects:
        pid = project.get("id", "")
        paths = list(dict.fromkeys(project_paths.get(pid, [])))
        if not paths:
            continue

        html_files: list[Path] = []
        for raw in paths:
            html_files.extend(html_candidates_from_path(raw))
        html_files = list(dict.fromkeys([p for p in html_files if p.exists()]))

        best_url = ""
        if html_files:
            for html in html_files:
                try:
                    text = html.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                best_url = extract_preferred_url(text)
                if best_url:
                    break
            if not best_url:
                best_url = html_files[0].resolve().as_uri()

        if best_url and should_replace_link(project.get("webLinks"), best_url):
            label = "Сайт проекта" if best_url.startswith("http") else "Локальная страница"
            project["webLinks"] = [{"label": label, "url": best_url}]


def derive_archive_root(destination_paths: list[str]) -> Path | None:
    for dst in destination_paths:
        norm = normalize_path(dst)
        marker = "\\project_archive\\"
        idx = norm.find(marker)
        if idx == -1:
            continue
        root = dst[: idx + len(marker) - 1]
        p = Path(root)
        if p.exists():
            return p
    return None


def build_dataset(bundle: SourceBundle) -> dict[str, Any]:
    workspace_root = bundle.base_projects_json.parent
    projects_index_rows = read_csv(bundle.projects_index)
    workflows_rows = read_csv(bundle.workflows_index)
    chats_rows = read_csv(bundle.chats_index)
    org_rows = read_csv(bundle.organization_audit)
    base = read_json(bundle.base_projects_json, {"projects": [], "ideas": [], "upgradePaths": []})
    profile = load_system_profile(workspace_root)
    translation_map = profile.get("projectTitleTranslations", {})
    telegram_data = read_json(workspace_root / DEFAULT_TELEGRAM_INTELLIGENCE, {})
    web_links = extract_web_links(workspace_root)
    idea_inbox = read_json(workspace_root / "data" / "idea_inbox.json", {"ideas": []})

    ideas = list(base.get("ideas", []))
    known_idea_keys = {
        str(item.get("id") or item.get("title") or "").strip().casefold()
        for item in ideas
        if isinstance(item, dict)
    }
    for item in idea_inbox.get("ideas", []) if isinstance(idea_inbox, dict) else []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        key = str(item.get("id") or title).strip().casefold()
        if key in known_idea_keys:
            continue
        ideas.append(
            {
                "id": str(item.get("id") or slugify(title, "idea")),
                "title": title,
                "description": str(item.get("description") or item.get("comment") or "").strip(),
                "tags": item.get("tags", []) or ([item["group"]] if item.get("group") else []),
                "priority": str(item.get("priority") or "medium"),
                "relatedProject": str(item.get("relatedProject", "")).strip(),
                "addedDate": str(item.get("addedDate") or date.today().isoformat()),
            }
        )
        known_idea_keys.add(key)

    manual_projects = ensure_priority_projects(base.get("projects", []), profile)
    manual_by_title: dict[str, dict[str, Any]] = {}
    for project in manual_projects:
        for key in ("title", "originalTitle", "sourceTitle"):
            value = str(project.get(key, "")).strip().casefold()
            if value:
                manual_by_title[value] = project

    project_rows_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    projects_by_chat_id: dict[str, set[str]] = defaultdict(set)

    for row in projects_index_rows:
        name_key = str(row.get("project_name", "")).strip().casefold()
        if name_key:
            project_rows_by_name[name_key].append(row)
        for chat_id in split_semicolon(row.get("related_chat_ids")):
            if row.get("project_name"):
                projects_by_chat_id[chat_id].add(str(row["project_name"]).strip())

    project_items: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    title_to_project_id: dict[str, str] = {}

    for row in org_rows:
        source_title = str(row.get("project", "")).strip()
        if not source_title:
            continue
        title, original_title = localize_project_title(source_title, translation_map)
        name_key = source_title.casefold()
        manual = manual_by_title.get(name_key, {})
        linked_rows = project_rows_by_name.get(name_key, [])

        source_exists = to_bool(row.get("source_exists"))
        destination_exists = to_bool(row.get("destination_exists"))
        migration_status = str(row.get("status", "")).strip()

        statuses = [str(r.get("status", "")).strip().lower() for r in linked_rows if r.get("status")]
        preferred_status = statuses[0] if statuses else str(manual.get("status", "")).strip().lower()
        status = map_status(migration_status, preferred_status)

        manual_progress = manual.get("progress")
        if isinstance(manual_progress, (int, float)):
            manual_progress = int(manual_progress)
        else:
            manual_progress = None

        progress = map_progress(status, source_exists, destination_exists, manual_progress)
        topic = str(row.get("topic", "manual")).strip().lower() or "manual"
        category = str(manual.get("category", "")).strip() or category_from_topic(topic)

        related_chat_ids: list[str] = []
        related_chat_dates: list[str] = []
        related_workflow_paths: list[str] = []
        for linked in linked_rows:
            related_chat_ids.extend(split_semicolon(linked.get("related_chat_ids")))
            related_chat_dates.extend(split_semicolon(linked.get("related_chat_dates")))
            related_workflow_paths.extend(split_semicolon(linked.get("workflow_paths")))
        related_chat_ids = list(dict.fromkeys(related_chat_ids))
        related_workflow_paths = [p for p in dict.fromkeys(related_workflow_paths) if is_specific_path(p)]

        title_slug = slugify(source_title, fallback="project")
        project_id = title_slug
        i = 2
        while project_id in used_ids:
            project_id = f"{title_slug}-{i}"
            i += 1
        used_ids.add(project_id)
        register_project_lookup(title_to_project_id, project_id, source_title, title, original_title)

        tags = []
        tags.extend([t for t in manual.get("tags", []) if isinstance(t, str)])
        tags.extend([topic, migration_status or "unknown"])
        if related_chat_ids:
            tags.append("chat-linked")
        if related_workflow_paths:
            tags.append("workflow-linked")
        tags = [t for t in dict.fromkeys([t for t in tags if t])]

        notes = join_unique_notes(
            manual.get("notes", ""),
            row.get("notes", ""),
            *(linked.get("notes", "") for linked in linked_rows),
        )
        description = (
            str(manual.get("description", "")).strip()
            or summarize_text(row.get("notes"), 220)
            or "Проект из объединенного AI Workspace."
        )
        last_updated = str(manual.get("lastUpdated", "")).strip() or latest_date(related_chat_dates)

        key_tasks = manual.get("keyTasks")
        if not key_tasks:
            key_tasks = [
                {"task": "Проверен исходный путь проекта", "done": source_exists},
                {"task": "Папка проекта доступна в project_archive", "done": destination_exists},
                {"task": "Привязаны связанные чаты", "done": bool(related_chat_ids)},
                {"task": "Привязаны связанные workflows", "done": bool(related_workflow_paths)},
            ]

        item = {
            "id": project_id,
            "title": title,
            "originalTitle": original_title,
            "sourceTitle": source_title,
            "description": description,
            "status": status,
            "progress": progress,
            "category": category,
            "topic": topic,
            "tags": tags,
            "lastUpdated": last_updated,
            "keyTasks": key_tasks,
            "notes": notes,
            "sourcePath": row.get("source_path", ""),
            "destinationPath": row.get("destination_path", ""),
            "sourceExists": source_exists,
            "destinationExists": destination_exists,
            "migrationStatus": migration_status,
            "relatedChatIds": related_chat_ids,
            "relatedWorkflowPaths": related_workflow_paths,
            "relatedChatsCount": len(related_chat_ids),
            "relatedWorkflowsCount": len(related_workflow_paths),
        }
        item_links = web_links.get(project_id)
        if item_links:
            item["webLinks"] = item_links
        project_items.append(
            {
                **item,
            }
        )

    existing_titles = {
        value
        for project in project_items
        for value in (
            str(project.get("title", "")).strip().casefold(),
            str(project.get("originalTitle", "")).strip().casefold(),
            str(project.get("sourceTitle", "")).strip().casefold(),
        )
        if value
    }
    for manual in manual_projects:
        source_title = str(manual.get("sourceTitle") or manual.get("originalTitle") or manual.get("title", "")).strip()
        localized_title = str(manual.get("title", "")).strip()
        title = localized_title or source_title
        if not title or title.casefold() in existing_titles or source_title.casefold() in existing_titles:
            continue
        display_title, derived_original = localize_project_title(title, translation_map)
        original_title = str(manual.get("originalTitle", "")).strip() or derived_original
        title = display_title
        title_slug = slugify(source_title or title, fallback="manual")
        project_id = title_slug
        i = 2
        while project_id in used_ids:
            project_id = f"{title_slug}-{i}"
            i += 1
        used_ids.add(project_id)
        register_project_lookup(title_to_project_id, project_id, title, original_title, source_title)

        status = str(manual.get("status", "research")).strip().lower()
        if status not in STATUS_RU:
            status = "research"

        manual_item = {
            "id": project_id,
            "title": title,
            "originalTitle": original_title,
            "sourceTitle": source_title or title,
            "description": str(manual.get("description", "")).strip() or "Ручной проект.",
            "status": status,
            "progress": int(manual.get("progress", 30)),
            "category": str(manual.get("category", "")).strip() or TOPIC_LABELS["manual"],
            "topic": "manual",
            "tags": list(dict.fromkeys([*(manual.get("tags", []) or []), "manual"])),
            "lastUpdated": str(manual.get("lastUpdated", "")).strip() or date.today().isoformat(),
            "keyTasks": manual.get("keyTasks", []),
            "notes": join_unique_notes(manual.get("notes", "")),
            "sourcePath": "",
            "destinationPath": "",
            "sourceExists": False,
            "destinationExists": False,
            "migrationStatus": "manual_only",
            "relatedChatIds": [],
            "relatedWorkflowPaths": [],
            "relatedChatsCount": 0,
            "relatedWorkflowsCount": 0,
        }
        manual_links = web_links.get(project_id)
        if manual_links:
            manual_item["webLinks"] = manual_links
        project_items.append(
            {
                **manual_item,
            }
        )

    known_destinations = {normalize_path(p.get("destinationPath", "")) for p in project_items if p.get("destinationPath")}
    archive_root = derive_archive_root(
        [str(r.get("destination_path", "")) for r in org_rows if r.get("destination_path")]
    )
    if archive_root and archive_root.exists():
        skip_topics = {"_migration_reports", "configs"}
        for topic_dir in archive_root.iterdir():
            if not topic_dir.is_dir():
                continue
            topic = topic_dir.name.strip().lower()
            if topic in skip_topics:
                continue
            for project_dir in topic_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                norm_dest = normalize_path(str(project_dir))
                if norm_dest in known_destinations:
                    continue
                if any(
                    normalize_path(str(p.get("destinationPath", ""))).startswith(norm_dest + "\\")
                    for p in project_items
                    if p.get("destinationPath")
                ):
                    continue

                raw_title = project_dir.name.replace("_", " ").strip()
                source_title = raw_title if raw_title else project_dir.name
                title, original_title = localize_project_title(source_title, translation_map)
                title_slug = slugify(source_title, fallback="project")
                project_id = title_slug
                i = 2
                while project_id in used_ids:
                    project_id = f"{title_slug}-{i}"
                    i += 1
                used_ids.add(project_id)
                register_project_lookup(title_to_project_id, project_id, title, original_title, source_title)
                known_destinations.add(norm_dest)

                autodiscovered_item = {
                    "id": project_id,
                    "title": title,
                    "originalTitle": original_title,
                    "sourceTitle": source_title,
                    "description": "Автообнаруженный проект из project_archive.",
                    "status": "research",
                    "progress": 25,
                    "category": category_from_topic(topic),
                    "topic": topic if topic in TOPIC_LABELS else "manual",
                    "tags": ["autodiscovered", topic],
                    "lastUpdated": date.today().isoformat(),
                    "keyTasks": [
                        {"task": "Проект обнаружен в project_archive", "done": True},
                        {"task": "Требуется уточнить карточку проекта", "done": False},
                    ],
                    "notes": "",
                    "sourcePath": "",
                    "destinationPath": str(project_dir),
                    "sourceExists": False,
                    "destinationExists": True,
                    "migrationStatus": "autodiscovered",
                    "relatedChatIds": [],
                    "relatedWorkflowPaths": [],
                    "relatedChatsCount": 0,
                    "relatedWorkflowsCount": 0,
                }
                auto_links = web_links.get(project_id)
                if auto_links:
                    autodiscovered_item["webLinks"] = auto_links
                project_items.append(
                    {
                        **autodiscovered_item,
                    }
                )

    project_alias_paths: dict[str, list[str]] = {}
    for project in project_items:
        aliases = []
        for key in ("sourcePath", "destinationPath"):
            p = project.get(key)
            if is_specific_path(p):
                aliases.append(str(p))
        lookup_name = str(project.get("sourceTitle") or project.get("originalTitle") or project["title"]).strip().casefold()
        for row in project_rows_by_name.get(lookup_name, []):
            root_path = row.get("project_root_path", "")
            if is_specific_path(root_path):
                aliases.append(root_path)
        aliases = list(dict.fromkeys(aliases))
        project_alias_paths[project["id"]] = aliases

    chat_items: list[dict[str, Any]] = []
    chats_by_id: dict[str, dict[str, Any]] = {}
    project_to_chat_ids: dict[str, set[str]] = defaultdict(set)

    for row in chats_rows:
        chat_id = str(row.get("chat_id", "")).strip()
        if not chat_id:
            continue

        related_project_ids: set[str] = set()
        for name in projects_by_chat_id.get(chat_id, set()):
            pid = title_to_project_id.get(name.casefold())
            if pid:
                related_project_ids.add(pid)

        referenced_paths = split_semicolon(row.get("referenced_paths"))
        workflow_paths = split_semicolon(row.get("workflow_paths"))
        path_tokens = [*referenced_paths, *workflow_paths]

        for pid, aliases in project_alias_paths.items():
            if any(path_related(token, alias) for token in path_tokens for alias in aliases):
                related_project_ids.add(pid)

        for pid in related_project_ids:
            project_to_chat_ids[pid].add(chat_id)

        item = {
            "id": chat_id,
            "date": str(row.get("date", "")).strip(),
            "theme": str(row.get("theme", "")).strip(),
            "title": str(row.get("title", "")).strip() or "Untitled chat",
            "summary": summarize_text(row.get("summary"), 260),
            "recoveryStatus": str(row.get("recovery_status", "")).strip(),
            "conversationPath": str(row.get("conversation_path", "")).strip(),
            "brainPath": str(row.get("brain_path", "")).strip(),
            "workflowPaths": workflow_paths,
            "referencedPaths": referenced_paths,
            "relatedProjectIds": sorted(related_project_ids),
        }
        chat_items.append(item)
        chats_by_id[chat_id] = item

    attach_fallback_web_links(project_items, chat_items)

    workflow_items: list[dict[str, Any]] = []
    project_to_workflow_ids: dict[str, set[str]] = defaultdict(set)
    seen_workflow_paths: set[str] = set()

    for idx, row in enumerate(workflows_rows, start=1):
        name = str(row.get("workflow_name", "")).strip() or f"workflow-{idx}"
        workflow_path = str(row.get("workflow_path", "")).strip()
        path_key = normalize_path(workflow_path)
        if path_key and path_key in seen_workflow_paths:
            continue
        if path_key:
            seen_workflow_paths.add(path_key)
        workflow_id = f"{slugify(name, 'workflow')}-{idx}"
        related_paths = split_semicolon(row.get("related_project_paths"))
        related_chat_ids = split_semicolon(row.get("related_chat_ids"))
        related_project_ids: set[str] = set()

        for pid, aliases in project_alias_paths.items():
            if any(path_related(token, alias) for token in related_paths for alias in aliases):
                related_project_ids.add(pid)

        for chat_id in related_chat_ids:
            chat = chats_by_id.get(chat_id)
            if chat:
                related_project_ids.update(chat.get("relatedProjectIds", []))

        for pid in related_project_ids:
            project_to_workflow_ids[pid].add(workflow_id)

        workflow_items.append(
            {
                "id": workflow_id,
                "name": name,
                "path": workflow_path,
                "source": str(row.get("source", "")).strip(),
                "notes": summarize_text(row.get("notes"), 260),
                "relatedProjectPaths": related_paths,
                "relatedChatIds": related_chat_ids,
                "relatedChatTitles": split_semicolon(row.get("related_chat_titles")),
                "relatedProjectIds": sorted(related_project_ids),
            }
        )

    existing_workflow_paths = {
        normalize_path(w.get("path", "")) for w in workflow_items if is_specific_path(w.get("path", ""))
    }
    fallback_seq = len(workflow_items) + 1
    for project in project_items:
        dest = project.get("destinationPath", "")
        if not is_specific_path(dest):
            continue
        pid = project["id"]
        for rel in (".agents\\workflows", ".agent\\workflows", "workflows"):
            wf_dir = Path(dest) / rel
            if not wf_dir.exists() or not wf_dir.is_dir():
                continue
            for wf_file in wf_dir.iterdir():
                if not wf_file.is_file():
                    continue
                if wf_file.suffix.lower() not in {".md", ".json", ".yaml", ".yml"}:
                    continue
                norm_wf_path = normalize_path(str(wf_file))
                if norm_wf_path in existing_workflow_paths:
                    continue
                existing_workflow_paths.add(norm_wf_path)
                wid = f"{slugify(wf_file.stem, 'workflow')}-{fallback_seq}"
                fallback_seq += 1
                workflow_items.append(
                    {
                        "id": wid,
                        "name": wf_file.name,
                        "path": str(wf_file),
                        "source": "filesystem_scan",
                        "notes": "Автообнаружен в папке workflows.",
                        "relatedProjectPaths": [dest],
                        "relatedChatIds": [],
                        "relatedChatTitles": [],
                        "relatedProjectIds": [pid],
                    }
                )
                project_to_workflow_ids[pid].add(wid)

    uuid_like = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
    known_chat_ids = set(chats_by_id.keys())
    brain_roots: list[Path] = []
    for row in chats_rows:
        bp = str(row.get("brain_path", "")).strip()
        if bp and Path(bp).exists():
            brain_roots.append(Path(bp).parent)
    default_brain = Path(r"C:\Users\Admin\.gemini\antigravity\brain")
    if default_brain.exists():
        brain_roots.append(default_brain)
    brain_roots = list(dict.fromkeys(brain_roots))

    for brain_root in brain_roots:
        for chat_dir in brain_root.iterdir():
            if not chat_dir.is_dir():
                continue
            chat_id = chat_dir.name
            if chat_id in known_chat_ids:
                continue
            if not uuid_like.match(chat_id):
                continue
            md_candidates = [
                p
                for p in chat_dir.rglob("*.md")
                if ".tempmediastorage" not in str(p).lower() and not p.name.endswith(".metadata.md")
            ]
            if not md_candidates:
                continue
            md_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            title, summary = extract_title_summary_from_md(md_candidates[0])

            chat_item = {
                "id": chat_id,
                "date": date.fromtimestamp(chat_dir.stat().st_mtime).isoformat(),
                "theme": "Новая сессия",
                "title": title,
                "summary": summary,
                "recoveryStatus": "auto-discovered",
                "conversationPath": "",
                "brainPath": str(chat_dir),
                "workflowPaths": [],
                "referencedPaths": [str(p) for p in md_candidates[:5]],
                "relatedProjectIds": [],
            }
            chat_items.append(chat_item)
            chats_by_id[chat_id] = chat_item
            known_chat_ids.add(chat_id)

    inferred_chat_links = autolink_chat_project_ids(chat_items, project_items, project_alias_paths)
    project_to_chat_ids = defaultdict(set)
    for chat in chat_items:
        for pid in chat.get("relatedProjectIds", []) or []:
            project_to_chat_ids[pid].add(chat["id"])

    for project in project_items:
        pid = project["id"]
        chat_ids = sorted(project_to_chat_ids.get(pid, set()) | set(project.get("relatedChatIds", [])))
        workflow_ids = sorted(project_to_workflow_ids.get(pid, set()))
        project["relatedChatIds"] = chat_ids
        project["relatedChatsCount"] = len(chat_ids)
        project["relatedWorkflowIds"] = workflow_ids
        project["relatedWorkflowsCount"] = len(workflow_ids)

    project_items, chat_items, workflow_items, ideas, consolidation = archive_and_consolidate_sources(
        project_items,
        chat_items,
        workflow_items,
        ideas,
    )
    obsidian_entities = apply_obsidian_overlays(project_items, chat_items, workflow_items, bundle.obsidian_root)
    inferred_chat_links += autolink_chat_project_ids(chat_items, project_items, project_alias_paths)
    sanitize_related_project_ids(project_items, chat_items, workflow_items)
    rebuild_project_relationships(project_items, chat_items, workflow_items)
    project_groups = build_project_groups(project_items)

    chat_items.sort(key=lambda c: (parse_date(c.get("date")) or date.min, c.get("id")), reverse=True)
    workflow_items.sort(key=lambda w: w.get("name", "").casefold())
    status_order = {"active": 0, "research": 1, "paused": 2, "backlog": 3, "done": 4}
    project_items.sort(key=lambda p: (p.get("groupTitle", ""), status_order.get(p["status"], 99), p["title"].casefold()))

    ideas, idea_router = build_idea_router(profile, project_items, ideas)
    project_registry = build_project_registry(project_items, chat_items, workflow_items, bundle.obsidian_root)
    graph = build_graph(project_items, chat_items, workflow_items)
    monitoring = build_monitoring_layer(profile, project_items, ideas, telegram_data, idea_router, consolidation, project_groups)

    return {
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "lastUpdated": date.today().isoformat(),
            "linking": {
                "inferredChatLinks": inferred_chat_links,
            },
            "sources": {
                "projectsIndex": str(bundle.projects_index),
                "workflowsIndex": str(bundle.workflows_index),
                "chatsIndex": str(bundle.chats_index),
                "organizationAudit": str(bundle.organization_audit),
            },
        },
        "stats": {
            "projects": len(project_items),
            "chats": len(chat_items),
            "workflows": len(workflow_items),
            "activeProjects": sum(1 for p in project_items if p["status"] == "active"),
            "missingProjects": sum(1 for p in project_items if p.get("migrationStatus") == "missing_source_and_destination"),
            "archivedProjects": consolidation["summary"].get("archivedProjects", 0),
            "archivedChats": consolidation["summary"].get("archivedChats", 0),
        },
        "projects": project_items,
        "projectGroups": project_groups,
        "chats": chat_items,
        "workflows": workflow_items,
        "ideas": ideas,
        "upgradePaths": base.get("upgradePaths", []),
        "monitoring": monitoring,
        "ideaRouter": idea_router,
        "projectRegistry": project_registry,
        "obsidianEntities": {
            "projects": [build_note_ref(record) for _, record in sorted(obsidian_entities["projects_by_id"].items())],
            "chats": [build_note_ref(record) for _, record in sorted(obsidian_entities["chats_by_id"].items())],
            "workflows": [build_note_ref(record) for _, record in sorted(obsidian_entities["workflows_by_id"].items())],
        },
        "archives": consolidation.get("archives", []),
        "consolidation": consolidation.get("summary", {}),
        "graph": graph,
    }


def build_monitoring_layer(
    profile: dict[str, Any],
    projects: list[dict[str, Any]],
    ideas: list[dict[str, Any]],
    telegram_data: dict[str, Any],
    idea_router: dict[str, Any],
    consolidation: dict[str, Any],
    project_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    telegram_summary = telegram_data.get("summary", {}) if isinstance(telegram_data, dict) else {}
    telegram_stats = telegram_data.get("stats", {}) if isinstance(telegram_data, dict) else {}
    telegram_sources = telegram_data.get("sources", []) if isinstance(telegram_data, dict) else []

    active_projects = [project["title"] for project in projects if project.get("status") == "active"][:6]
    current_focus = active_projects or [project["title"] for project in projects[:6]]
    source_highlights = [source.get("title", "") for source in telegram_sources[:5] if source.get("title")]

    cadence = profile.get("reviewCadence", {}) or {}
    cadence_items = [
        {"label": "Ежедневно", "value": cadence.get("daily", "")},
        {"label": "Еженедельно", "value": cadence.get("weekly", "")},
        {"label": "Ежемесячно", "value": cadence.get("monthly", "")},
    ]
    cadence_items = [item for item in cadence_items if item["value"]]

    recommendations = list_unique(
        [
            *(profile.get("bestPracticeRecommendations", []) or []),
            *(telegram_summary.get("recommendations", []) or []),
        ]
    )[:8]

    skill_candidates = [item for item in (profile.get("skillCandidates", []) or []) if isinstance(item, dict)]
    for item in (telegram_data.get("skillSuggestions", []) if isinstance(telegram_data, dict) else [])[:3]:
        if not isinstance(item, dict):
            continue
        skill_candidates.append(
            {
                "id": f"telegram-{item.get('id') or slugify(item.get('title', 'skill'), 'skill')}",
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "why": item.get("why", ""),
                "basedOn": item.get("basedOn", []),
                "source": "telegram_intelligence",
            }
        )
    skill_candidates = list_unique(skill_candidates)[:8]

    project_hypotheses = [item for item in (profile.get("projectHypotheses", []) or []) if isinstance(item, dict)]
    for item in (telegram_data.get("projectSuggestions", []) if isinstance(telegram_data, dict) else [])[:3]:
        if not isinstance(item, dict):
            continue
        project_hypotheses.append(
            {
                "id": f"telegram-{slugify(item.get('title', 'project'), 'project')}",
                "title": item.get("title", ""),
                "category": item.get("category", "Новая гипотеза"),
                "summary": item.get("summary", ""),
                "why": item.get("why", ""),
                "basedOn": item.get("basedOn", []),
                "source": "telegram_intelligence",
            }
        )
    project_hypotheses = list_unique(project_hypotheses)[:8]

    return {
        "profile": {
            "title": profile.get("title", "Системная карта интересов"),
            "summary": profile.get("summary", ""),
            "roles": profile.get("roles", []),
            "lifeAreas": profile.get("lifeAreas", []),
            "focusThemes": profile.get("focusThemes", []),
            "interestSignals": profile.get("interestSignals", []),
            "noiseFilters": profile.get("noiseFilters", []),
            "monitoringSources": profile.get("monitoringSources", []),
            "reviewCadence": cadence_items,
            "currentFocusProjects": current_focus,
            "sourceHighlights": source_highlights,
        },
        "stats": {
            "activeProjects": sum(1 for project in projects if project.get("status") == "active"),
            "ideas": len(ideas),
            "trackedSources": telegram_stats.get("uniqueSources", 0),
            "archivedProjects": consolidation.get("summary", {}).get("archivedProjects", 0),
            "archivedChats": consolidation.get("summary", {}).get("archivedChats", 0),
        },
        "processingProtocol": profile.get("processingProtocol", []),
        "routingRules": profile.get("routingRules", []),
        "recommendations": recommendations,
        "skillSuggestions": skill_candidates,
        "projectSuggestions": project_hypotheses,
        "ideaRouterSummary": idea_router.get("summary", {}),
        "ideaRouterRecommendations": idea_router.get("recommendations", []),
        "projectGroups": project_groups,
        "consolidation": consolidation.get("summary", {}),
    }


def build_system_profile_markdown(data: dict[str, Any]) -> str:
    monitoring = data.get("monitoring", {})
    profile = monitoring.get("profile", {})
    stats = monitoring.get("stats", {})
    idea_router = data.get("ideaRouter", {})
    router_summary = idea_router.get("summary", {})

    lines = [
        "# Системная карта интересов",
        "",
        f"- Обновлено: **{data['meta']['generatedAt']}**",
        f"- Активных проектов: **{stats.get('activeProjects', 0)}**",
        f"- Идей в базе: **{stats.get('ideas', 0)}**",
        f"- Отслеживаемых источников: **{stats.get('trackedSources', 0)}**",
        "",
        "## Суть",
        profile.get("summary", ""),
        "",
    ]

    if profile.get("roles"):
        lines.extend(["## Роли", *[f"- {item}" for item in profile["roles"]], ""])
    if profile.get("focusThemes"):
        lines.extend(["## Приоритетные темы", *[f"- {item}" for item in profile["focusThemes"]], ""])
    if profile.get("interestSignals"):
        lines.extend(["## Что считать сильным сигналом", *[f"- {item}" for item in profile["interestSignals"]], ""])
    if profile.get("noiseFilters"):
        lines.extend(["## Что считать шумом", *[f"- {item}" for item in profile["noiseFilters"]], ""])
    if profile.get("monitoringSources"):
        lines.extend(["## Источники мониторинга", *[f"- {item}" for item in profile["monitoringSources"]], ""])
    if profile.get("currentFocusProjects"):
        lines.extend(["## Текущий фокус", *[f"- {item}" for item in profile["currentFocusProjects"]], ""])
    if profile.get("reviewCadence"):
        lines.extend(
            [
                "## Ритм обзора",
                *[f"- {item['label']}: {item['value']}" for item in profile["reviewCadence"]],
                "",
            ]
        )
    if router_summary:
        lines.extend(
            [
                "",
                "## Текущее состояние маршрутизации идей",
                f"- Идей в triage: **{router_summary.get('totalIdeas', 0)}**",
                f"- Кластеров: **{router_summary.get('clusterCount', 0)}**",
                f"- В обновление проектов: **{router_summary.get('routedToProject', 0)}**",
                f"- В skill-кандидаты: **{router_summary.get('skillCandidates', 0)}**",
                f"- В проектные гипотезы: **{router_summary.get('projectHypotheses', 0)}**",
                f"- В заметки: **{router_summary.get('referenceNotes', 0)}**",
                f"- В архив: **{router_summary.get('archiveItems', 0)}**",
            ]
        )

    if idea_router.get("recommendations"):
        lines.extend(["", "## Приоритеты idea router"])
        for item in idea_router["recommendations"]:
            lines.append(f"- {item}")

    return "\n".join(lines).rstrip() + "\n"


def build_information_ops_markdown(data: dict[str, Any]) -> str:
    monitoring = data.get("monitoring", {})
    profile = monitoring.get("profile", {})
    idea_router = data.get("ideaRouter", {})
    router_summary = idea_router.get("summary", {})

    lines = [
        "# Информационный контур",
        "",
        f"- Обновлено: **{data['meta']['generatedAt']}**",
        f"- Профиль: **{profile.get('title', 'Системная карта интересов')}**",
        "",
        "## Правило обработки новой информации",
    ]
    for step in monitoring.get("processingProtocol", []):
        lines.append(f"- **{step.get('step', '')}** — {step.get('detail', '')}")

    if monitoring.get("routingRules"):
        lines.extend(["", "## Маршрутизация входящего"])
        for item in monitoring["routingRules"]:
            lines.append(
                f"- **{item.get('when', '')}** → {item.get('route', '')}. {item.get('action', '')}".strip()
            )

    if monitoring.get("recommendations"):
        lines.extend(["", "## Рекомендации"])
        for item in monitoring["recommendations"]:
            lines.append(f"- {item}")

    if monitoring.get("skillSuggestions"):
        lines.extend(["", "## Новые навыки для агентов"])
        for item in monitoring["skillSuggestions"]:
            title = item.get("title", "")
            code = item.get("code") or item.get("id") or ""
            suffix = f" (`{code}`)" if code else ""
            lines.append(f"- **{title}**{suffix} — {item.get('summary', '')}")

    if monitoring.get("projectSuggestions"):
        lines.extend(["", "## Проектные гипотезы"])
        for item in monitoring["projectSuggestions"]:
            category = item.get("category", "")
            suffix = f" [{category}]" if category else ""
            lines.append(f"- **{item.get('title', '')}**{suffix} — {item.get('summary', '')}")

    if router_summary:
        lines.extend(
            [
                "",
                "## Статус маршрутизации идей",
                f"- Идей в triage: **{router_summary.get('totalIdeas', 0)}**",
                f"- В обновление проектов: **{router_summary.get('routedToProject', 0)}**",
                f"- В skill-кандидаты: **{router_summary.get('skillCandidates', 0)}**",
                f"- В проектные гипотезы: **{router_summary.get('projectHypotheses', 0)}**",
                f"- В заметки: **{router_summary.get('referenceNotes', 0)}**",
                f"- В архив: **{router_summary.get('archiveItems', 0)}**",
            ]
        )

    if monitoring.get("projectGroups"):
        lines.extend(["", "## Группы связанных проектов"])
        for group in monitoring.get("projectGroups", [])[:8]:
            lines.append(
                f"- **{group.get('title', '')}** — проектов: {group.get('projectCount', 0)}, активных: {group.get('activeProjects', 0)}"
            )

    consolidation = monitoring.get("consolidation", {}) or {}
    if consolidation:
        lines.extend(
            [
                "",
                "## Очистка и консолидация",
                f"- Архивировано проектов: **{consolidation.get('archivedProjects', 0)}**",
                f"- Архивировано чатов: **{consolidation.get('archivedChats', 0)}**",
                f"- Объединено проектов: **{consolidation.get('projectMerges', 0)}**",
                f"- Объединено чатов: **{consolidation.get('chatMerges', 0)}**",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def build_idea_router_markdown(data: dict[str, Any]) -> str:
    router = data.get("ideaRouter", {})
    summary = router.get("summary", {})
    queue = router.get("queue", [])
    clusters = router.get("clusters", [])

    lines = [
        "# Маршрутизация идей AI Workspace",
        "",
        f"- Обновлено: **{data['meta']['generatedAt']}**",
        f"- Идей в triage: **{summary.get('totalIdeas', 0)}**",
        f"- Кластеров: **{summary.get('clusterCount', 0)}**",
        f"- Проектных обновлений: **{summary.get('routedToProject', 0)}**",
        f"- Skill-кандидатов: **{summary.get('skillCandidates', 0)}**",
        f"- Проектных гипотез: **{summary.get('projectHypotheses', 0)}**",
        f"- Заметок: **{summary.get('referenceNotes', 0)}**",
        f"- Архива: **{summary.get('archiveItems', 0)}**",
        "",
        "## Очередь разбора",
    ]

    if queue:
        for item in queue:
            suffix = f" → {item['relatedProject']}" if item.get("relatedProject") else ""
            lines.append(
                f"- **{item['title']}** [{item['routeLabel']}] ({item.get('lifeAreaLabel', '—')} / {item.get('themeLabel', '—')}){suffix} — {item.get('nextStep', '')}"
            )
    else:
        lines.append("- Нет идей в очереди.")

    lines.extend(["", "## Кластеры"])
    if clusters:
        for cluster in clusters:
            tags = ", ".join(cluster.get("topTags", []) or [])
            titles = ", ".join(cluster.get("ideaTitles", []) or [])
            lines.extend(
                [
                    f"### {cluster['title']}",
                    f"- Идей: **{cluster.get('ideaCount', 0)}**",
                    f"- Жизненная зона: {cluster.get('lifeAreaLabel', '—')}",
                    f"- Тема: {cluster.get('themeLabel', '—')}",
                    f"- Базовый исход: {cluster.get('routeBiasLabel', '—')}",
                    f"- Следующий шаг: {cluster.get('nextStep', '—')}",
                    *([f"- Теги: {tags}"] if tags else []),
                    *([f"- Примеры: {titles}"] if titles else []),
                    "",
                ]
            )
    else:
        lines.append("- Кластеров пока нет.")

    return "\n".join(lines).rstrip() + "\n"


def build_graph(projects: list[dict[str, Any]], chats: list[dict[str, Any]], workflows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    edge_keys: set[tuple[str, str, str]] = set()

    root_id = "root-ai-workspace"
    nodes.append({"id": root_id, "label": "AI Workspace", "type": "root", "topic": "root", "size": 26})

    topic_nodes: dict[str, str] = {}
    for project in projects:
        topic = project.get("topic") or "manual"
        if topic not in topic_nodes:
            topic_id = f"topic-{slugify(topic)}"
            topic_nodes[topic] = topic_id
            nodes.append(
                {
                    "id": topic_id,
                    "label": TOPIC_LABELS.get(topic, topic),
                    "type": "topic",
                    "topic": topic,
                    "size": 20,
                }
            )
            edge = (root_id, topic_id, "contains")
            if edge not in edge_keys:
                edges.append({"source": edge[0], "target": edge[1], "kind": edge[2]})
                edge_keys.add(edge)

    for project in projects:
        node_id = f"project-{project['id']}"
        nodes.append(
            {
                "id": node_id,
                "label": project["title"],
                "type": "project",
                "topic": project.get("topic", "manual"),
                "size": 12 + min(project.get("relatedChatsCount", 0), 8),
                "status": project.get("status"),
            }
        )
        topic_id = topic_nodes.get(project.get("topic", "manual"), topic_nodes.get("manual"))
        if topic_id:
            edge = (topic_id, node_id, "contains")
            if edge not in edge_keys:
                edges.append({"source": edge[0], "target": edge[1], "kind": edge[2]})
                edge_keys.add(edge)

    for workflow in workflows:
        node_id = f"workflow-{workflow['id']}"
        nodes.append(
            {
                "id": node_id,
                "label": workflow["name"],
                "type": "workflow",
                "topic": "workflow",
                "size": 10,
            }
        )
        related = workflow.get("relatedProjectIds", [])
        if not related:
            edge = (root_id, node_id, "orphan")
            if edge not in edge_keys:
                edges.append({"source": edge[0], "target": edge[1], "kind": edge[2]})
                edge_keys.add(edge)
        for pid in related:
            edge = (f"project-{pid}", node_id, "workflow")
            if edge not in edge_keys:
                edges.append({"source": edge[0], "target": edge[1], "kind": edge[2]})
                edge_keys.add(edge)

    for chat in chats:
        node_id = f"chat-{chat['id']}"
        nodes.append(
            {
                "id": node_id,
                "label": chat.get("title") or chat["id"],
                "type": "chat",
                "topic": (chat.get("theme") or "chat").split("/")[0],
                "size": 8,
                "date": chat.get("date", ""),
            }
        )
        related = chat.get("relatedProjectIds", [])
        if not related:
            edge = (root_id, node_id, "chat")
            if edge not in edge_keys:
                edges.append({"source": edge[0], "target": edge[1], "kind": edge[2]})
                edge_keys.add(edge)
        for pid in related:
            edge = (f"project-{pid}", node_id, "chat")
            if edge not in edge_keys:
                edges.append({"source": edge[0], "target": edge[1], "kind": edge[2]})
                edge_keys.add(edge)

    return {"nodes": nodes, "edges": edges}


def export_obsidian(obsidian_root: Path, data: dict[str, Any], refresh_entities: bool = False) -> dict[str, int]:
    projects_dir = obsidian_root / "Projects" / "AI Workspace"
    chats_dir = obsidian_root / "Chats" / "AI Workspace"
    workflows_dir = obsidian_root / "Workflows" / "AI Workspace"
    dashboards_dir = obsidian_root / "Dashboards"
    config_dir = obsidian_root / "Config"
    for folder in (projects_dir, chats_dir, workflows_dir, dashboards_dir, config_dir):
        folder.mkdir(parents=True, exist_ok=True)

    def resolve_note_filename(item: dict[str, Any], fallback_name: str) -> str:
        kb_note = item.get("kbNote") or {}
        relative_path = str(kb_note.get("relativePath") or "").strip()
        if relative_path:
            return Path(relative_path).name
        note_name = str(kb_note.get("noteName") or "").strip()
        if note_name:
            return f"{note_name}.md"
        return fallback_name

    def write_entity_note(path: Path, content: str) -> None:
        if refresh_entities or not path.exists():
            path.write_text(content, encoding="utf-8")

    project_note_name: dict[str, str] = {}
    for p in data["projects"]:
        note_name = resolve_note_filename(p, f"{safe_filename(p['id'], 'project')}.md")
        project_note_name[p["id"]] = note_name

    chat_note_name: dict[str, str] = {}
    for c in data["chats"]:
        note_name = resolve_note_filename(c, f"{safe_filename(c.get('title') or c['id'], 'chat')}-{c['id'][:8]}.md")
        chat_note_name[c["id"]] = note_name

    workflow_note_name: dict[str, str] = {}
    for w in data["workflows"]:
        note_name = resolve_note_filename(w, f"{safe_filename(w['name'], 'workflow')}-{w['id'].split('-')[-1]}.md")
        workflow_note_name[w["id"]] = note_name

    for p in data["projects"]:
        lines = [
            "---",
            "type: project",
            f"id: {p['id']}",
            f"title: \"{yaml_safe(p['title'])}\"",
            f"original_title: \"{yaml_safe(p.get('originalTitle') or '')}\"",
            f"topic: {p.get('topic','manual')}",
            f"status: {p.get('status','research')}",
            f"source_exists: {str(bool(p.get('sourceExists'))).lower()}",
            f"destination_exists: {str(bool(p.get('destinationExists'))).lower()}",
            f"related_chats: {p.get('relatedChatsCount',0)}",
            f"related_workflows: {p.get('relatedWorkflowsCount',0)}",
            f"updated: {data['meta']['lastUpdated']}",
            "---",
            "",
            f"# {p['title']}",
            "",
            *([f"_Оригинальное название: {p['originalTitle']}_" , ""] if p.get("originalTitle") else []),
            f"- Статус: **{STATUS_RU.get(p.get('status','research'),'Исследование')}**",
            f"- Категория: {p.get('category','')}",
            f"- Migration: `{p.get('migrationStatus','')}`",
            f"- Source: `{p.get('sourcePath','')}`",
            f"- Destination: `{p.get('destinationPath','')}`",
            "",
            "## Описание",
            p.get("description", ""),
            "",
            "## Задачи",
        ]
        for t in p.get("keyTasks", []) or []:
            mark = "x" if t.get("done") else " "
            lines.append(f"- [{mark}] {t.get('task','')}")

        if p.get("notes"):
            lines.extend(["", "## Заметки", p["notes"]])

        if p.get("relatedChatIds"):
            lines.extend(["", "## Связанные чаты"])
            for cid in p["relatedChatIds"][:80]:
                if cid in chat_note_name:
                    lines.append(f"- [[{chat_note_name[cid][:-3]}]]")
                else:
                    lines.append(f"- `{cid}`")

        if p.get("relatedWorkflowIds"):
            lines.extend(["", "## Связанные workflows"])
            for wid in p["relatedWorkflowIds"][:80]:
                if wid in workflow_note_name:
                    lines.append(f"- [[{workflow_note_name[wid][:-3]}]]")
                else:
                    lines.append(f"- `{wid}`")

        write_entity_note(projects_dir / project_note_name[p["id"]], "\n".join(lines))

    for c in data["chats"]:
        lines = [
            "---",
            "type: chat",
            f"id: {c['id']}",
            f"date: {c.get('date','')}",
            f"theme: \"{yaml_safe(c.get('theme') or '')}\"",
            f"recovery_status: {c.get('recoveryStatus','')}",
            "---",
            "",
            f"# {c.get('title') or c['id']}",
            "",
            c.get("summary", ""),
            "",
            "## Пути",
            f"- Conversation: `{c.get('conversationPath','')}`",
            f"- Brain: `{c.get('brainPath','')}`",
        ]
        if c.get("relatedProjectIds"):
            lines.extend(["", "## Проекты"])
            for pid in c["relatedProjectIds"]:
                note = project_note_name.get(pid)
                if note:
                    lines.append(f"- [[{note[:-3]}]]")
        write_entity_note(chats_dir / chat_note_name[c["id"]], "\n".join(lines))

    for w in data["workflows"]:
        lines = [
            "---",
            "type: workflow",
            f"id: {w['id']}",
            f"name: \"{yaml_safe(w['name'])}\"",
            f"source: {w.get('source','')}",
            "---",
            "",
            f"# {w['name']}",
            "",
            f"- Path: `{w.get('path','')}`",
            f"- Source: `{w.get('source','')}`",
        ]
        if w.get("notes"):
            lines.extend(["", "## Notes", w["notes"]])
        if w.get("relatedProjectIds"):
            lines.extend(["", "## Проекты"])
            for pid in w["relatedProjectIds"]:
                note = project_note_name.get(pid)
                if note:
                    lines.append(f"- [[{note[:-3]}]]")
        write_entity_note(workflows_dir / workflow_note_name[w["id"]], "\n".join(lines))

    project_index_lines = [
        "# AI Workspace Projects",
        "",
        f"Обновлено: {data['meta']['generatedAt']}",
        "",
    ]
    for p in data["projects"]:
        note = project_note_name[p["id"]][:-3]
        project_index_lines.append(
            f"- [[{note}]] — {STATUS_RU.get(p.get('status', 'research'), p.get('status','research'))}, чатов: {p.get('relatedChatsCount',0)}, workflows: {p.get('relatedWorkflowsCount',0)}"
        )
    (projects_dir / "00_INDEX.md").write_text("\n".join(project_index_lines), encoding="utf-8")

    chat_index_lines = ["# AI Workspace Chats", "", f"Обновлено: {data['meta']['generatedAt']}", ""]
    for c in data["chats"]:
        note = chat_note_name[c["id"]][:-3]
        chat_index_lines.append(f"- [[{note}]] — {c.get('date','')} — {c.get('theme','')}")
    (chats_dir / "00_INDEX.md").write_text("\n".join(chat_index_lines), encoding="utf-8")

    workflow_index_lines = ["# AI Workspace Workflows", "", f"Обновлено: {data['meta']['generatedAt']}", ""]
    for w in data["workflows"]:
        note = workflow_note_name[w["id"]][:-3]
        workflow_index_lines.append(f"- [[{note}]] — {w.get('source','')}")
    (workflows_dir / "00_INDEX.md").write_text("\n".join(workflow_index_lines), encoding="utf-8")

    mindmap_lines = ["mindmap", "  root((AI Workspace))"]
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in data["projects"]:
        by_topic[p.get("topic", "manual")].append(p)
    for topic, projects in sorted(by_topic.items()):
        mindmap_lines.append(f"    {TOPIC_LABELS.get(topic, topic)}")
        for p in projects:
            mindmap_lines.append(f"      {p['title']}")

    overview_lines = [
        "# AI Workspace Overview",
        "",
        f"- Обновлено: **{data['meta']['generatedAt']}**",
        f"- Проектов: **{data['stats']['projects']}**",
        f"- Чатов: **{data['stats']['chats']}**",
        f"- Workflows: **{data['stats']['workflows']}**",
        "",
        "## Разделы",
        "- [[Projects/AI Workspace/00_INDEX]]",
        "- [[Chats/AI Workspace/00_INDEX]]",
        "- [[Workflows/AI Workspace/00_INDEX]]",
        "",
        "## Mindmap (Mermaid)",
        "```mermaid",
        *mindmap_lines,
        "```",
    ]
    ideas_lines = [
        "# Идеи AI Workspace",
        "",
        f"Обновлено: {data['meta']['generatedAt']}",
        "",
    ]
    for idea in data.get("ideas", []):
        title = idea.get("title", "Идея")
        description = idea.get("description", "")
        related = idea.get("relatedProject", "")
        tags = ", ".join(idea.get("tags", []) or [])
        ideas_lines.append(f"## {title}")
        if description:
            ideas_lines.append(description)
        if related:
            ideas_lines.append(f"- Связанный проект: {related}")
        if tags:
            ideas_lines.append(f"- Теги: {tags}")
        ideas_lines.append("")

    
    groups_lines = [
        "# Группы связанных проектов AI Workspace",
        "",
        f"Обновлено: {data['meta']['generatedAt']}",
        "",
    ]
    for group in data.get("projectGroups", []):
        groups_lines.append(f"## {group.get('title', 'Группа')}")
        groups_lines.append(f"- Проектов: {group.get('projectCount', 0)}")
        groups_lines.append(f"- Активных: {group.get('activeProjects', 0)}")
        if group.get("projectTitles"):
            groups_lines.append(f"- Состав: {', '.join(group.get('projectTitles', [])[:8])}")
        groups_lines.append("")

    archive_lines = [
        "# Архив источников AI Workspace",
        "",
        f"Обновлено: {data['meta']['generatedAt']}",
        "",
    ]
    for item in data.get("archives", []):
        title = item.get("title") or item.get("id") or "source"
        reason = item.get("reason", "")
        kind = item.get("kind", "")
        merged_into = item.get("mergedInto", "")
        suffix = f" -> {merged_into}" if merged_into else ""
        archive_lines.append(f"- [{kind}] {title} :: {reason}{suffix}")
    if len(archive_lines) == 4:
        archive_lines.append("- Архив пуст.")
    (dashboards_dir / "AI Workspace Overview.md").write_text("\n".join(overview_lines), encoding="utf-8")
    (config_dir / "Системная карта интересов.md").write_text(build_system_profile_markdown(data), encoding="utf-8")
    (dashboards_dir / "Информационный контур.md").write_text(build_information_ops_markdown(data), encoding="utf-8")
    (dashboards_dir / "Идеи AI Workspace.md").write_text("\n".join(ideas_lines).rstrip() + "\n", encoding="utf-8")
    (dashboards_dir / "Группы проектов AI Workspace.md").write_text("\n".join(groups_lines).rstrip() + "\n", encoding="utf-8")
    (dashboards_dir / "Архив источников AI Workspace.md").write_text("\n".join(archive_lines).rstrip() + "\n", encoding="utf-8")
    (dashboards_dir / "Weekly Project Brief.md").write_text(
        build_weekly_project_brief(data.get("projects", []), data["meta"]["generatedAt"]),
        encoding="utf-8",
    )

    (dashboards_dir / "Маршрутизация идей AI Workspace.md").write_text(build_idea_router_markdown(data), encoding="utf-8")

    return {
        "project_notes": len(project_note_name),
        "chat_notes": len(chat_note_name),
        "workflow_notes": len(workflow_note_name),
    }


def save_compat_projects_json(path: Path, data: dict[str, Any]) -> None:
    payload = {
        "meta": {
            "lastUpdated": data["meta"]["lastUpdated"],
            "version": "2.0-generated",
        },
        "stats": data.get("stats", {}),
        "upgradePaths": data.get("upgradePaths", []),
        "ideas": data.get("ideas", []),
        "monitoring": data.get("monitoring", {}),
        "ideaRouter": data.get("ideaRouter", {}),
        "projectGroups": data.get("projectGroups", []),
        "projectRegistry": data.get("projectRegistry", {}),
        "archives": data.get("archives", []),
        "consolidation": data.get("consolidation", {}),
        "projects": data.get("projects", []),
    }
    write_json(path, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync AI Workspace indexes into dashboard + Obsidian knowledge base.")
    parser.add_argument("--projects-index", help="Path to projects_index.csv")
    parser.add_argument("--workflows-index", help="Path to workflows_index.csv")
    parser.add_argument("--chats-index", help="Path to antigravity_chat_index.csv")
    parser.add_argument("--organization-audit", help="Path to organization_audit_*.csv")
    parser.add_argument("--base-projects-json", help="Path to manual projects base JSON (default: projects_manual_base.json)")
    parser.add_argument("--out-dashboard-json", help="Path for generated dashboard_data.json")
    parser.add_argument("--out-mindmap-json", help="Path for generated mindmap.json")
    parser.add_argument("--out-projects-json", help="Path for generated compatibility projects.json (default: projects.json)")
    parser.add_argument("--out-project-registry-json", help="Path for generated project_registry.json")
    parser.add_argument("--obsidian-root", default=str(DEFAULT_OBSIDIAN_ROOT), help="Obsidian vault root path")
    parser.add_argument("--no-obsidian-export", action="store_true", help="Skip markdown export into Obsidian vault")
    parser.add_argument(
        "--refresh-obsidian-entities",
        action="store_true",
        help="Rewrite existing project/chat/workflow entity notes in Obsidian instead of preserving them",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(__file__).resolve().parents[2]
    bundle = resolve_sources(workspace_root, args)
    if args.out_project_registry_json:
        bundle.out_project_registry_json = Path(args.out_project_registry_json)
    ensure_manual_base_seeded(bundle.base_projects_json, bundle.out_projects_json)
    data = build_dataset(bundle)
    monitoring_report = workspace_root / "docs" / f"information_operating_system_{data['meta']['lastUpdated']}.md"
    weekly_report = workspace_root / "docs" / "weekly_project_brief.md"

    write_json(bundle.out_dashboard_json, data)
    write_json(bundle.out_mindmap_json, data["graph"])
    save_compat_projects_json(bundle.out_projects_json, data)
    write_json(bundle.out_project_registry_json, data["projectRegistry"])
    monitoring_report.parent.mkdir(parents=True, exist_ok=True)
    monitoring_report.write_text(build_information_ops_markdown(data), encoding="utf-8")
    weekly_report.write_text(
        build_weekly_project_brief(data.get("projects", []), data["meta"]["generatedAt"]),
        encoding="utf-8",
    )

    obsidian_stats = None
    if not args.no_obsidian_export:
        obsidian_stats = export_obsidian(
            bundle.obsidian_root,
            data,
            refresh_entities=args.refresh_obsidian_entities,
        )

    print(f"DASHBOARD_JSON: {bundle.out_dashboard_json}")
    print(f"MINDMAP_JSON: {bundle.out_mindmap_json}")
    print(f"PROJECTS_JSON: {bundle.out_projects_json}")
    print(f"PROJECT_REGISTRY_JSON: {bundle.out_project_registry_json}")
    print(f"MONITORING_REPORT: {monitoring_report}")
    print(f"WEEKLY_REPORT: {weekly_report}")
    if obsidian_stats is not None:
        print(f"OBSIDIAN_ROOT: {bundle.obsidian_root}")
        print(
            "OBSIDIAN_NOTES: "
            f"projects={obsidian_stats['project_notes']} "
            f"chats={obsidian_stats['chat_notes']} "
            f"workflows={obsidian_stats['workflow_notes']}"
        )
    print(
        "COUNTS: "
        f"projects={data['stats']['projects']} "
        f"chats={data['stats']['chats']} "
        f"workflows={data['stats']['workflows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

