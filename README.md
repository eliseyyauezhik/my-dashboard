# Мой Дашборд (AI Workspace)

## Как запустить локально

Важно: если открыть `index.html` двойным кликом (как `file://`), браузер обычно блокирует загрузку `data/*.json`.

Запуск через встроенный сервер (рекомендуется):

```powershell
.\start_dashboard.ps1 -Open
```

Быстрый вариант через двойной клик:

- `start_dashboard.cmd`

## Доступ с телефона

Если телефон в той же Wi‑Fi сети:

```powershell
.\start_dashboard.ps1 -Lan
```

Скрипт покажет `LAN_URL` с IP этого ПК. Откройте его на телефоне в браузере.
Если не открывается, обычно мешает Windows Firewall и/или профиль сети `Public`.

Через мобильный интернет “из любой точки” локальный сервер недоступен — нужен внешний хостинг или туннель с постоянно включенным ПК.

Альтернатива без PowerShell-обертки:

```powershell
python .\scripts\dashboard\dashboard_server.py --port 8891
```

## Как обновить данные

Сгенерировать `data/dashboard_data.json`, `data/mindmap.json`, обновить `projects.json`:

```powershell
python .\scripts\dashboard\sync_workspace_data.py
```

или

```powershell
.\scripts\dashboard\sync_workspace_data.ps1
```

## Хостинг

См. `docs/hosting.md`.

Для постоянного доступа с телефона через 4G оптимальный путь: `GitHub Pages` для статики + прокси/CDN перед ним, если нужен свой домен или сетевой слой.
Операционная памятка: `docs/remote_access_4g.md`.
Публичная выгрузка теперь собирается через `scripts/dashboard/build_public_site.mjs` и скрывает локальные пути из JSON.
Если домен и прокси у вас уже в Cloudflare, используйте `Cloudflare Pages`: инструкция в `docs/cloudflare_pages_setup.md`.
