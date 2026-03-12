#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_GOVERNANCE_CONFIG = Path("config/agent_data_governance.json")
DEFAULT_OBSIDIAN_ROOT = Path(r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase")
WORKSPACE_DOC = Path("docs/universal_agent_operating_regulation.md")
WORKSPACE_SUMMARY_DOC = Path("docs/agent_governance_checklist.md")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def build_regulation_markdown(data: dict[str, Any], generated_at: str) -> str:
    lines = [
        f"# {data['title']}",
        "",
        f"- Версия: **{data.get('version', '1.0')}**",
        f"- Обновлено: **{generated_at}**",
        "",
        "## Суть",
        data.get("summary", ""),
        "",
        "## Источники истины",
        *bullets(data.get("sourceOfTruth", [])),
        "",
        "## Базовые принципы агентов",
        *bullets(data.get("agentPrinciples", [])),
        "",
        "## Правила записи",
    ]

    for key, value in (data.get("writePolicy", {}) or {}).items():
        lines.append(f"- **{key}**: {value}")

    lines.extend(["", "## Исходы маршрутизации", *bullets(data.get("routingOutcomes", [])), ""])

    backup = data.get("backupPolicy", {}) or {}
    lines.extend(["## Резервирование и восстановление"])
    for key, value in backup.items():
        if key == "cadence":
            continue
        lines.append(f"- **{key}**: {value}")
    cadence = backup.get("cadence", {}) or {}
    if cadence:
        lines.extend(["", "### Ритм snapshot-политики"])
        for key, value in cadence.items():
            lines.append(f"- **{key}**: {value}")

    review = data.get("reviewPolicy", {}) or {}
    if review:
        lines.extend(["", "## Ревизия и обслуживание"])
        for key, items in review.items():
            lines.append(f"### {key.capitalize()}")
            lines.extend(bullets(items))
            lines.append("")
        if lines[-1] == "":
            lines.pop()

    security = data.get("securityPolicy", {}) or {}
    if security:
        lines.extend(["", "## Безопасность и уязвимости"])
        for key, value in security.items():
            lines.append(f"- **{key}**: {value}")

    quality = data.get("qualityChecks", []) or []
    if quality:
        lines.extend(["", "## Обязательные проверки", *bullets(quality)])

    loops = data.get("automationLoops", []) or []
    if loops:
        lines.extend(["", "## Автоконтуры"])
        for item in loops:
            lines.append(f"- **{item.get('name', '')}**: {item.get('purpose', '')}")
            lines.append(f"  Скрипт: `{item.get('script', '')}`")
            lines.append(f"  Задача: `{item.get('task', '')}`")

    risks = data.get("knownRisks", []) or []
    if risks:
        lines.extend(["", "## Известные риски", *bullets(risks)])

    agreement = data.get("agreementPoints", []) or []
    if agreement:
        lines.extend(["", "## Точки соглашения", *bullets(agreement)])

    return "\n".join(lines).rstrip() + "\n"


def build_checklist_markdown(data: dict[str, Any], generated_at: str) -> str:
    lines = [
        "# Чеклист агентной работы",
        "",
        f"Обновлено: {generated_at}",
        "",
        "## Перед работой",
        "- Прочитать `config/agent_data_governance.json` и `config/personal_system_profile.json`.",
        "- Понять, относится ли входящий материал к проекту, идее, note, skill или архиву.",
        "- Определить, нужен ли snapshot перед изменениями.",
        "",
        "## Во время работы",
        "- Новые идеи сохранять в `data/idea_inbox.json` или через `/api/idea-inbox`.",
        "- Не плодить дубли проектов и заметок.",
        "- Использовать русское имя проекта как основное отображаемое.",
        "",
        "## После работы",
        "- Проверить `dashboard_data.json`, `projects.json`, ключевые Obsidian notes.",
        "- Обновить monitoring/knowledge layers через sync.",
        "- При рисках утечки секретов запустить governance audit.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def export_obsidian(obsidian_root: Path, regulation: str, checklist: str) -> None:
    config_dir = obsidian_root / "Config"
    dashboards_dir = obsidian_root / "Dashboards"
    config_dir.mkdir(parents=True, exist_ok=True)
    dashboards_dir.mkdir(parents=True, exist_ok=True)
    write_text(config_dir / "Универсальный регламент агентной работы.md", regulation)
    write_text(dashboards_dir / "Чеклист агентной работы.md", checklist)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build governance docs for agents and knowledge base.")
    parser.add_argument("--governance-config", default=str(DEFAULT_GOVERNANCE_CONFIG))
    parser.add_argument("--obsidian-root", default=str(DEFAULT_OBSIDIAN_ROOT))
    parser.add_argument("--no-obsidian-export", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = Path(__file__).resolve().parents[2]
    config_path = Path(args.governance_config)
    if not config_path.is_absolute():
      config_path = workspace_root / config_path

    generated_at = datetime.now().isoformat(timespec="seconds")
    data = read_json(config_path)
    regulation = build_regulation_markdown(data, generated_at)
    checklist = build_checklist_markdown(data, generated_at)

    workspace_doc = workspace_root / WORKSPACE_DOC
    workspace_summary = workspace_root / WORKSPACE_SUMMARY_DOC
    write_text(workspace_doc, regulation)
    write_text(workspace_summary, checklist)

    if not args.no_obsidian_export:
        export_obsidian(Path(args.obsidian_root), regulation, checklist)

    print(f"GOVERNANCE_DOC: {workspace_doc}")
    print(f"GOVERNANCE_CHECKLIST: {workspace_summary}")
    if not args.no_obsidian_export:
        print(f"OBSIDIAN_ROOT: {args.obsidian_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
