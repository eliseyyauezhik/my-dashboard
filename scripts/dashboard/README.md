# Dashboard Sync

Скрипт `sync_workspace_data.py` делает единый конвейер:
- читает индексы `projects_index.csv`, `workflows_index.csv`, `antigravity_chat_index.csv`;
- объединяет их с миграционным аудитом `organization_audit_*.csv`;
- генерирует:
  - `data/dashboard_data.json`
  - `data/mindmap.json`
  - обновлённый `projects.json` (совместимость);
- экспортирует markdown-слой в Obsidian vault (проекты/чаты/workflows + overview).

## Запуск

```powershell
python .\scripts\dashboard\sync_workspace_data.py
```

или через PowerShell-обёртку:

```powershell
.\scripts\dashboard\sync_workspace_data.ps1
```

Отключить экспорт в Obsidian:

```powershell
python .\scripts\dashboard\sync_workspace_data.py --no-obsidian-export
```

## Автообновление (Task Scheduler)

Создать задачу, которая запускает раз в 1 час:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\Admin\.gemini\antigravity\scratch\Мой Дашборд\scripts\dashboard\sync_workspace_data.ps1"
```

Рекомендуемые триггеры:
- при входе в систему;
- каждые 60 минут.

Быстрая регистрация задачи:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\dashboard\register_sync_task.ps1" -IntervalMinutes 60
```

## Локальный сервер дашборда

Чтобы `index.html` и `mindmap.html` стабильно загружали `data/*.json` (и работал `/api/idea-inbox`), запускайте сервер:

```powershell
.\start_dashboard.ps1 -Open
```

или напрямую:

```powershell
python .\scripts\dashboard\dashboard_server.py --port 8891
```
