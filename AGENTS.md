# Workspace Protocol

Для этого workspace действуют дополнительные правила поверх базовых системных инструкций.

## Source Of Truth

- База знаний: `D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase`
- Операционный workspace дашборда: `C:\Users\Admin\.gemini\antigravity\scratch\Мой Дашборд`
- Входящий слой новых идей: `data/idea_inbox.json`

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

## Safety

- Для snapshot/restore использовать `scripts/versioning/snapshot.ps1` и `scripts/versioning/restore.ps1`.
- Для периодических проверок использовать `scripts/governance/run_governance_audit.ps1`.
- Для обновления контуров мониторинга использовать `scripts/dashboard/sync_all_sources.ps1`.
