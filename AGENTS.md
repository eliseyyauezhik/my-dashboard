<!-- PRIORITY: repo_root/AGENTS.md > workspace/agents.md > scratch-dashboard/AGENTS.md -->
# Workspace Protocol

Для этого workspace действуют дополнительные правила поверх базовых системных инструкций.

## Source Of Truth

- База знаний: `D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase`
- Операционный workspace дашборда: `C:\Users\Admin\.gemini\antigravity\scratch\Мой Дашборд`
- Входящий слой новых идей: `data/idea_inbox.json`
- Ручной input для project overrides: `projects_manual_base.json`
- `projects.json`, `data/dashboard_data.json` и `data/project_registry.json` — generated views; вручную их не редактировать

## Mandatory Reading

Перед работой с базой знаний, project archive, мониторингом или идеями агент должен опираться на:

- `config/agent_data_governance.json`
- `config/personal_system_profile.json`
- `docs/universal_agent_operating_regulation.md`

## Write Rules

- Новые идеи и комментарии сначала идут в `data/idea_inbox.json` или `/api/idea-inbox`.
- Русское название проекта используется как основное отображаемое; английское сохраняется в `originalTitle`.
- Нельзя создавать новую проектную сущность, не проверив связь с существующим проектом, idea, note или skill.
- Перед restore, rollback или крупной перезаписью нужно создать snapshot.
- После изменения source-of-truth сначала обновляй канонические заметки или `projects_manual_base.json`, затем запускай `scripts/dashboard/sync_workspace_data.py`.
- Ручные правки структуры проектов вносятся в `projects_manual_base.json`, а не в `projects.json`.

## Interaction Rules

- **Агент должен всегда отвечать на русском языке.** Это приоритетное правило для всех коммуникаций в этом workspace.

## Safety

- Для snapshot/restore использовать `scripts/versioning/snapshot.ps1` и `scripts/versioning/restore.ps1`.
- Для периодических проверок использовать `scripts/governance/run_governance_audit.ps1`.
- Для обновления контуров мониторинга использовать `scripts/dashboard/sync_all_sources.ps1`.
