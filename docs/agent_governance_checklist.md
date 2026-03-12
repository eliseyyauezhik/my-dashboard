# Чеклист агентной работы

Обновлено: 2026-03-10T03:09:18

## Перед работой
- Прочитать `config/agent_data_governance.json` и `config/personal_system_profile.json`.
- Понять, относится ли входящий материал к проекту, идее, note, skill или архиву.
- Определить, нужен ли snapshot перед изменениями.

## Во время работы
- Новые идеи сохранять в `data/idea_inbox.json` или через `/api/idea-inbox`.
- Не плодить дубли проектов и заметок.
- Использовать русское имя проекта как основное отображаемое.

## После работы
- Проверить `dashboard_data.json`, `projects.json`, ключевые Obsidian notes.
- Обновить monitoring/knowledge layers через sync.
- При рисках утечки секретов запустить governance audit.
