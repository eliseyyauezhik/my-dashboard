# Умный Хаб Знаний (Monitoring Hub) — Подробная инструкция для реализации

> **Для кого**: ИИ-программист (Antigravity, Cursor, Claude или другой агент).
> **Цель**: Построить персональную систему мониторинга информации по темам пользователя.
> **Контекст проекта**: Пользователь — архитектор AI-проектов, разработчик агентных систем, организатор образовательных и семейных контуров. У него ~22 активных проекта, Telegram как основной источник информации, Obsidian KB.

---

## КРИТИЧЕСКИЕ ПРАВИЛА (прочитай перед началом работы)

> [!CAUTION]
>
> 1. **НЕ поднимай VPS** на первых фазах. Используй бесплатные облачные тиры (n8n Cloud, Supabase Free). VPS — только когда лимиты будут исчерпаны.
> 2. **НЕ пиши код там, где есть готовая нода n8n**. Проверяй библиотеку нод перед написанием custom code.
> 3. **НЕ дублируй данные** между Supabase и Obsidian. Supabase = структурированные данные для API/поиска. Obsidian = человекочитаемые заметки.
> 4. **НЕ создавай новых сущностей** (проекты, идеи, навыки) без проверки связи с существующими. Всегда сначала `SELECT * FROM projects WHERE title ILIKE '%keyword%'`.
> 5. **Инкрементальность**: каждая фаза должна быть usable сама по себе. Не жди завершения всех фаз.
> 6. **НЕ храни секреты в коде**. API-ключи — только через переменные окружения (n8n credentials, Supabase env).

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        ИСТОЧНИКИ                                │
│  Telegram каналы  ·  RSS-ленты  ·  YouTube  ·  Ручной ввод     │
└──────────┬──────────────┬──────────────┬──────────────┬─────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    n8n Cloud (бесплатно)                         │
│                                                                 │
│  Workflow 1: Telegram Webhook → AI-сжатие → Supabase           │
│  Workflow 2: RSS Polling → AI-фильтрация → Supabase            │
│  Workflow 3: Supabase → Obsidian .md файлы                     │
│  Workflow 4: Weekly Digest → Telegram бот → Пользователю       │
│  Workflow 5: Резерв                                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase (бесплатно)                          │
│                                                                 │
│  Таблицы: signals, projects, ideas, sources, digests            │
│  pgvector: embeddings для RAG-поиска                            │
│  Realtime: подписки для дашборда                                │
│  Edge Functions: embed-on-insert триггер                        │
│  Row Level Security: приватность данных                         │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐        ┌──────────────────────────────┐
│   Дашборд            │        │   Obsidian                    │
│   (GitHub Pages)     │        │   (Локально + Syncthing)      │
│                      │        │                                │
│   fetch → Supabase   │        │   .md заметки с тегами        │
│   Realtime updates   │        │   Граф связей                  │
│   RAG-поиск          │        │   Plugins: Dataview,           │
│   Мобильный доступ   │        │     Smart Connections          │
└──────────────────────┘        └──────────────────────────────┘
```

---

## Темы пользователя для мониторинга

При настройке фильтрации и AI-классификации использовать эти зоны:

| Зона жизни | Ключевые темы | Примеры источников |
|---|---|---|
| **Работа** | AI-агенты, skills, RAG, n8n, образование, гранты, продукты | Aimasters.Me, ИИшенка, Никита Велс AI |
| **Я** | Личное развитие, инструменты, база знаний, планирование | Saved Messages, Боты |
| **Семья** | Дом, дети, события, подарки, семейные решения | ДЕТИ, Мой Дом, Подарки |

### Что считать сигналом (включать)

- Связь с уже активным проектом или идеей
- Повторяющийся паттерн → кандидат в skill
- Потенциал экономить время/деньги
- Может быть использовано в течение 30 дней

### Что считать шумом (отбрасывать)

- Сырой поток без понятного действия
- Единичные вдохновляющие сообщения без паттерна
- Дубликаты и пересохранённые материалы
- Темы вне зон: я, семья, работа

---

## ФАЗА 1: Supabase — база данных (День 1)

### 1.1 Создание проекта

1. Зайти на [supabase.com](https://supabase.com), войти через GitHub (`eliseyyauezhik`)
2. Create new project:
   - Name: `monitoring-hub`
   - Region: **Frankfurt** (ближе к РФ)
   - Password: сгенерировать и сохранить

3. Записать credentials:
   - `SUPABASE_URL` = `https://xxxxx.supabase.co`
   - `SUPABASE_ANON_KEY` = (из Settings → API)
   - `SUPABASE_SERVICE_ROLE_KEY` = (из Settings → API, **не палить в коде!**)

### 1.2 Схема базы данных

Выполнить в SQL Editor Supabase:

```sql
-- Расширение для векторного поиска
create extension if not exists vector;

-- =============================================
-- Таблица: sources (источники мониторинга)
-- =============================================
create table sources (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  type text not null check (type in ('telegram_channel', 'telegram_chat', 'rss', 'youtube', 'manual')),
  url text,
  telegram_chat_id bigint,
  life_area text check (life_area in ('я', 'семья', 'работа')),
  theme text,
  is_active boolean default true,
  rank_score int default 50 check (rank_score between 0 and 100),
  last_fetched_at timestamptz,
  created_at timestamptz default now()
);

-- =============================================
-- Таблица: signals (входящие сигналы)
-- =============================================
create table signals (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id),
  original_text text not null,
  summary text,
  tags text[] default '{}',
  life_area text check (life_area in ('я', 'семья', 'работа')),
  theme text,
  signal_type text check (signal_type in ('news', 'tool', 'idea', 'pattern', 'resource', 'event')),
  relevance_score int default 50 check (relevance_score between 0 and 100),
  route text check (route in ('project_update', 'new_idea', 'skill_candidate', 'reference_note', 'archive', 'pending')),
  routed_to_project text,
  next_step text,
  is_duplicate boolean default false,
  original_date timestamptz,
  embedding vector(768),
  synced_to_obsidian boolean default false,
  created_at timestamptz default now()
);

-- =============================================
-- Таблица: projects (зеркало проектов дашборда)
-- =============================================
create table projects (
  id text primary key,
  title text not null,
  description text,
  status text default 'active',
  category text,
  tags text[] default '{}',
  progress int default 0,
  updated_at timestamptz default now()
);

-- =============================================
-- Таблица: digests (еженедельные сводки)
-- =============================================
create table digests (
  id uuid primary key default gen_random_uuid(),
  period_start date not null,
  period_end date not null,
  summary_text text,
  top_signals uuid[] default '{}',
  signal_count int default 0,
  created_at timestamptz default now()
);

-- =============================================
-- Индексы
-- =============================================
create index idx_signals_source on signals(source_id);
create index idx_signals_route on signals(route);
create index idx_signals_created on signals(created_at desc);
create index idx_signals_embedding on signals using ivfflat (embedding vector_cosine_ops) with (lists = 20);
create index idx_sources_type on sources(type);

-- =============================================
-- RPC для семантического поиска
-- =============================================
create or replace function match_signals(
  query_embedding vector(768),
  match_count int default 10,
  similarity_threshold float default 0.7
)
returns table (
  id uuid,
  summary text,
  tags text[],
  theme text,
  relevance_score int,
  route text,
  similarity float
)
language sql stable
as $$
  select
    s.id,
    s.summary,
    s.tags,
    s.theme,
    s.relevance_score,
    s.route,
    1 - (s.embedding <=> query_embedding) as similarity
  from signals s
  where 1 - (s.embedding <=> query_embedding) > similarity_threshold
    and s.embedding is not null
  order by s.embedding <=> query_embedding
  limit match_count;
$$;
```

### 1.3 Row Level Security

```sql
-- Включить RLS
alter table signals enable row level security;
alter table sources enable row level security;
alter table projects enable row level security;
alter table digests enable row level security;

-- Политика: service_role имеет полный доступ (для n8n)
-- anon key — только чтение (для дашборда)
create policy "anon_read_signals" on signals for select using (true);
create policy "anon_read_sources" on sources for select using (true);
create policy "anon_read_projects" on projects for select using (true);
create policy "anon_read_digests" on digests for select using (true);

-- Запись — только через service_role (n8n будет использовать его)
create policy "service_insert_signals" on signals for insert with check (true);
create policy "service_insert_sources" on sources for insert with check (true);
create policy "service_update_signals" on signals for update using (true);
```

### 1.4 Миграция существующих данных

Написать скрипт (Python или Node.js) который:

1. Читает `data/dashboard_data.json` (проекты, идеи, мониторинг)
2. Читает `data/telegram_intelligence.json` (23 источника)
3. Загружает в Supabase:
   - `projects` ← все проекты из `dashboard_data.json`
   - `sources` ← все Telegram-источники из `telegram_intelligence.json`
   - `signals` ← все существующие карточки знаний

> [!WARNING]
> **Типичная ошибка**: загружать всё в одну таблицу. Источники (sources) и сигналы (signals) — это РАЗНЫЕ сущности. Source = откуда берём. Signal = конкретная единица информации.

### 1.5 Проверка Фазы 1

```bash
# Должны вернуть данные:
curl "https://xxxxx.supabase.co/rest/v1/projects?select=id,title&limit=5" \
  -H "apikey: YOUR_ANON_KEY"

curl "https://xxxxx.supabase.co/rest/v1/sources?select=title,type&limit=5" \
  -H "apikey: YOUR_ANON_KEY"
```

---

## ФАЗА 2: n8n — Telegram Webhook (Дни 2–3)

### 2.1 Настройка n8n Cloud

1. Зайти на [n8n.cloud](https://n8n.cloud), создать бесплатный аккаунт
2. В Settings → Credentials добавить:
   - **Supabase**: URL + Service Role Key
   - **Telegram Bot API**: токен от @BotFather (создать бота `@MonitoringHubBot`)
   - **Google Gemini API** (или OpenRouter): ключ для AI-обработки

### 2.2 Workflow 1: «Telegram → AI → Supabase»

Логика:

```
Telegram Trigger (webhook)
       │
       ▼
  IF: message содержит текст/ссылку (не стикер, не фото без caption)
       │
       ▼
  Gemini: Сжать + классифицировать
       │  Промпт ниже ↓
       ▼
  IF: relevance_score >= 40
       │
       ├── YES → Supabase Insert (signals)
       │
       └── NO → Stop (не засоряем базу)
```

#### Промпт для AI-обработки сигнала

```
Ты — персональный ИИ-аналитик. Обработай входящее сообщение и верни JSON.

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:
- Зоны жизни: работа (AI, образование, агенты), я (инструменты, знания), семья (дом, дети)
- Активные проекты: Telegram-агрегатор, Мониторинг интересов, Дашборд, Карта технологий, ИИ-агент для гимназии, Грантовая презентация
- Фокус-темы: AI-агенты и skills, личная база знаний и RAG, идеи→проекты, образование и гранты

СООБЩЕНИЕ:
{{$json.message.text}}

ИСТОЧНИК: {{$json.message.chat.title || "Direct"}}

Верни ТОЛЬКО валидный JSON (без markdown, без комментариев):
{
  "summary": "1-2 предложения: суть + почему это полезно",
  "tags": ["тег1", "тег2", "тег3"],
  "life_area": "работа" | "я" | "семья",
  "theme": "краткая тема (AI, образование, дом, агенты, продуктивность, ...)",
  "signal_type": "news" | "tool" | "idea" | "pattern" | "resource" | "event",
  "relevance_score": 0-100,
  "route": "project_update" | "new_idea" | "skill_candidate" | "reference_note" | "archive",
  "routed_to_project": "название проекта если есть связь, иначе null",
  "next_step": "конкретное следующее действие",
  "is_duplicate": false
}

ПРАВИЛА ОЦЕНКИ:
- relevance_score 80-100: прямая связь с активным проектом + можно применить сегодня
- relevance_score 60-79: полезный паттерн или инструмент для одной из тем
- relevance_score 40-59: интересно, но без ясного действия
- relevance_score 0-39: шум, общие новости, не связано с зонами жизни

ПРАВИЛА МАРШРУТИЗАЦИИ (route):
- "project_update" — если есть прямая связь с активным проектом
- "new_idea" — сильный сигнал, но проекта ещё нет
- "skill_candidate" — повторяющийся паттерн для агента
- "reference_note" — полезно, но не тянет на проект
- "archive" — нет действия или связи
```

> [!IMPORTANT]
> **Типичная ошибка**: не парсить JSON ответ Gemini. Gemini иногда оборачивает ответ в ````json...````. Добавь ноду **Code** после Gemini:
>
> ```javascript
> const raw = $input.first().json.text || $input.first().json.response;
> const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
> return [{ json: JSON.parse(cleaned) }];
> ```

### 2.3 Нода Supabase Insert

Маппинг полей:

```
source_id       → lookup по telegram_chat_id или создать новый source
original_text   → {{$json.message.text}}
summary         → {{$('Gemini').json.summary}}
tags            → {{$('Gemini').json.tags}}
life_area       → {{$('Gemini').json.life_area}}
theme           → {{$('Gemini').json.theme}}
signal_type     → {{$('Gemini').json.signal_type}}
relevance_score → {{$('Gemini').json.relevance_score}}
route           → {{$('Gemini').json.route}}
routed_to_project → {{$('Gemini').json.routed_to_project}}
next_step       → {{$('Gemini').json.next_step}}
is_duplicate    → {{$('Gemini').json.is_duplicate}}
original_date   → {{$json.message.date}}
```

> [!WARNING]
> **Типичная ошибка**: не обрабатывать дубликаты. Добавь перед Insert проверку:
>
> ```sql
> SELECT id FROM signals
> WHERE original_text = $1
>   AND created_at > now() - interval '24 hours'
> LIMIT 1
> ```
>
> Если найден — пропустить.

### 2.4 Подключение каналов к боту

Два режима мониторинга Telegram:

**Режим A**: Пересылка вручную. Пользователь пересылает интересные сообщения боту → webhook срабатывает.

**Режим B**: Автоматический сбор. Для этого нужен Telegram userbot (Telethon/Pyrogram) — это **отдельный скрипт**, не n8n. Оставить на будущее (требует VPS).

Для MVP использовать **Режим A** — он работает без VPS и дополнительной инфраструктуры.

---

## ФАЗА 3: n8n — RSS мониторинг (День 4)

### 3.1 Workflow 2: «RSS → AI → Supabase»

```
Schedule Trigger (каждые 2 часа)
       │
       ▼
  RSS Feed Read (несколько URL)
       │
       ▼
  Split In Batches (по 5)
       │
       ▼
  Supabase: проверка дубликата (по url/title)
       │
       ▼
  IF: не дубликат
       │
       ▼
  Gemini: тот же промпт что в Фазе 2
       │
       ▼
  IF: relevance_score >= 40
       │
       ▼
  Supabase Insert (signals)
```

### 3.2 Рекомендуемые RSS-источники для старта

| Тема | RSS URL |
|---|---|
| AI News | `https://www.artificialintelligence-news.com/feed/` |
| Hacker News (AI) | `https://hnrss.org/newest?q=AI+agent+LLM` |
| n8n Blog | `https://n8n.io/blog/rss.xml` |
| Obsidian Roundup | `https://www.obsidianroundup.org/rss/` |
| Habr AI | `https://habr.com/ru/rss/hub/artificial_intelligence/all/` |
| Habr Education | `https://habr.com/ru/rss/hub/education/all/` |

> [!WARNING]
> **Типичная ошибка**: запрашивать все RSS разом. На бесплатном n8n есть лимит выполнений. Объединяй несколько лент в один workflow через **Merge** ноду. Интервал 2 часа, не чаще.

---

## ФАЗА 4: n8n → Obsidian (День 4–5)

### 4.1 Workflow 3: «Supabase → Obsidian .md»

```
Schedule Trigger (каждые 6 часов)
       │
       ▼
  Supabase: SELECT * FROM signals
            WHERE synced_to_obsidian = false
              AND route != 'archive'
              AND relevance_score >= 50
            ORDER BY created_at DESC
            LIMIT 20
       │
       ▼
  Code: сформировать Markdown
       │
       ▼
  Write File / HTTP Request (Obsidian REST API плагин)
       │
       ▼
  Supabase: UPDATE signals SET synced_to_obsidian = true WHERE id = ...
```

### 4.2 Формат Markdown-заметки для Obsidian

```markdown
---
tags: [{{tags через запятую}}]
source: "{{source_title}}"
life_area: "{{life_area}}"
theme: "{{theme}}"
route: "{{route}}"
relevance: {{relevance_score}}
date: {{created_at}}
project: "{{routed_to_project}}"
---

# {{summary — первое предложение как заголовок}}

{{summary — полный текст}}

## Следующий шаг
{{next_step}}

## Оригинал
{{original_text — первые 500 символов}}

---
*Автоматически создано Monitoring Hub · {{дата}}*
```

### 4.3 Структура папок в Obsidian

```
Obsidian Vault/
  MonitoringHub/
    Inbox/          ← новые сигналы попадают сюда
    Projects/       ← связанные с проектами
    Ideas/          ← новые идеи
    Skills/         ← кандидаты в навыки
    References/     ← справочные заметки
    Archive/        ← отработанное
```

Путь файла определяется по полю `route`:

- `project_update` → `MonitoringHub/Projects/{{routed_to_project}}/{{date}}-{{slug}}.md`
- `new_idea` → `MonitoringHub/Ideas/{{date}}-{{slug}}.md`
- `skill_candidate` → `MonitoringHub/Skills/{{date}}-{{slug}}.md`
- `reference_note` → `MonitoringHub/References/{{theme}}/{{date}}-{{slug}}.md`

### 4.4 Способы записи в Obsidian

**Вариант A (рекомендуемый)**: Obsidian Local REST API плагин

- Install: плагин `Local REST API` в Obsidian
- Obsidian должен быть открыт на десктопе
- n8n отправляет `HTTP Request` на `http://localhost:27123/vault/...`

**Вариант B**: Прямая запись в файловую систему

- Obsidian Vault синхронизирован через Syncthing/Yandex.Disk
- n8n (если на VPS/локально) пишет `.md` файлы напрямую

**Вариант C**: Через Git

- Obsidian Vault в git-репозитории
- n8n делает commit + push
- Obsidian Git плагин делает pull

Для MVP с n8n Cloud — **Вариант A** не подходит (n8n Cloud не видит localhost). Использовать **Вариант C** (Git) или отложить до перехода на VPS.

> [!IMPORTANT]
> **Временное решение для n8n Cloud**: Вместо прямой записи в Obsidian, n8n Cloud пишет в Supabase. Отдельный локальный скрипт (cron каждые 30 минут) тянет новые записи из Supabase и создаёт .md файлы в Obsidian Vault. Скрипт — простой Python:
>
> ```python
> import requests, os, json
> from datetime import datetime
>
> SUPABASE_URL = os.environ['SUPABASE_URL']
> SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
> OBSIDIAN_VAULT = r"C:\Users\Admin\ObsidianVault"
>
> # Fetch unsynced signals
> resp = requests.get(
>     f"{SUPABASE_URL}/rest/v1/signals",
>     params={"synced_to_obsidian": "eq.false", "route": "neq.archive", "order": "created_at.desc", "limit": "20"},
>     headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
> )
> signals = resp.json()
>
> for s in signals:
>     # Create .md file
>     folder_map = {"project_update": "Projects", "new_idea": "Ideas",
>                   "skill_candidate": "Skills", "reference_note": "References"}
>     folder = folder_map.get(s['route'], 'Inbox')
>     path = os.path.join(OBSIDIAN_VAULT, "MonitoringHub", folder)
>     os.makedirs(path, exist_ok=True)
>
>     slug = s['summary'][:60].replace(' ', '-').replace('/', '-') if s['summary'] else s['id'][:8]
>     date = datetime.fromisoformat(s['created_at']).strftime('%Y-%m-%d')
>     filename = f"{date}-{slug}.md"
>
>     content = f"""---
> tags: {json.dumps(s.get('tags', []), ensure_ascii=False)}
> theme: "{s.get('theme', '')}"
> route: "{s.get('route', '')}"
> relevance: {s.get('relevance_score', 0)}
> ---
>
> # {s.get('summary', 'Без заголовка')}
>
> ## Следующий шаг
> {s.get('next_step', '—')}
>
> ## Оригинал
> {(s.get('original_text', '') or '')[:500]}
> """
>     filepath = os.path.join(path, filename)
>     if not os.path.exists(filepath):
>         with open(filepath, 'w', encoding='utf-8') as f:
>             f.write(content)
>
>     # Mark as synced
>     requests.patch(
>         f"{SUPABASE_URL}/rest/v1/signals?id=eq.{s['id']}",
>         json={"synced_to_obsidian": True},
>         headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
>                  "Content-Type": "application/json", "Prefer": "return=minimal"}
>     )
>     print(f"Synced: {filename}")
> ```

---

## ФАЗА 5: Дашборд → Supabase (День 5–6)

### 5.1 Подключение дашборда к Supabase

В `index.html` добавить Supabase JS SDK:

```html
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

В `app.js` заменить `loadDashboardData()`:

```javascript
// Конфигурация Supabase
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJ...'; // anon key — безопасно хранить в клиенте
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Fallback: если Supabase недоступен, читаем локальный JSON
async function loadDashboardData() {
  try {
    const { data, error } = await supabase.from('projects').select('*');
    if (error) throw error;
    return { data: { projects: data }, source: 'supabase' };
  } catch (err) {
    console.warn('Supabase unavailable, falling back to JSON:', err);
    // Оригинальная логика загрузки JSON
    const res = await fetch('data/dashboard_data.json', { cache: 'no-store' });
    return { data: await res.json(), source: 'dashboard_data.json' };
  }
}
```

### 5.2 Realtime-подписки

```javascript
// Подписка на новые сигналы
supabase
  .channel('signals')
  .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'signals' }, (payload) => {
    // Показать уведомление о новом сигнале
    showNotification(`Новый сигнал: ${payload.new.summary}`);
    // Обновить счётчики
    refreshOverview();
  })
  .subscribe();
```

> [!WARNING]
> **Типичная ошибка**: класть service_role_key в клиентский JS. В дашборде — ТОЛЬКО anon key. Service role key — только в n8n credentials и серверных скриптах.

---

## ФАЗА 6: RAG-поиск (Дни 7–12)

### 6.1 Генерация эмбеддингов

Supabase Edge Function `embed-signal`:

```typescript
// supabase/functions/embed-signal/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const GEMINI_KEY = Deno.env.get('GEMINI_API_KEY')!;

serve(async (req) => {
  const { id, text } = await req.json();

  // Получить embedding от Gemini
  const embResp = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key=${GEMINI_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'models/text-embedding-004',
        content: { parts: [{ text }] },
      }),
    }
  );
  const { embedding } = await embResp.json();

  // Сохранить в Supabase
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  await supabase
    .from('signals')
    .update({ embedding: embedding.values })
    .eq('id', id);

  return new Response(JSON.stringify({ ok: true }));
});
```

### 6.2 Database Trigger: автоматическое эмбеддирование

```sql
-- Триггер: при вставке нового сигнала → вызвать Edge Function
create or replace function trigger_embed_signal()
returns trigger as $$
begin
  perform net.http_post(
    url := current_setting('app.settings.supabase_url') || '/functions/v1/embed-signal',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
      'Content-Type', 'application/json'
    ),
    body := jsonb_build_object(
      'id', NEW.id,
      'text', coalesce(NEW.summary, '') || ' ' || coalesce(NEW.original_text, '')
    )
  );
  return NEW;
end;
$$ language plpgsql security definer;

create trigger on_signal_insert
  after insert on signals
  for each row
  execute function trigger_embed_signal();
```

> [!WARNING]
> **Типичная ошибка**: использовать слишком большую размерность эмбеддинга. `text-embedding-004` от Gemini даёт 768 измерений — это оптимальный баланс качества и скорости. НЕ используй модели с 1536+ измерениями на бесплатном тире.

### 6.3 Поиск в дашборде

Добавить в `app.js`:

```javascript
async function semanticSearch(query) {
  // 1. Получить embedding запроса
  const embResp = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key=${GEMINI_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'models/text-embedding-004',
        content: { parts: [{ text: query }] },
      }),
    }
  );
  const { embedding } = await embResp.json();

  // 2. Найти похожие сигналы
  const { data, error } = await supabase.rpc('match_signals', {
    query_embedding: embedding.values,
    match_count: 10,
    similarity_threshold: 0.65,
  });

  return data;
}
```

> [!CAUTION]
> **Типичная ошибка**: вызывать Gemini Embedding API с клиента — это палит API-ключ. Вместо этого:
>
> - Создай Edge Function `search` которая принимает текстовый запрос, делает embed, и вызывает `match_signals`
> - Клиент вызывает только Edge Function, ключ Gemini остаётся на сервере

---

## ФАЗА 7: Weekly Digest (День 13)

### 7.1 Workflow 4: «Еженедельная сводка»

```
Schedule Trigger (каждый понедельник 09:00)
       │
       ▼
  Supabase: SELECT * FROM signals
            WHERE created_at > now() - interval '7 days'
              AND relevance_score >= 50
            ORDER BY relevance_score DESC
            LIMIT 30
       │
       ▼
  Gemini: "Составь еженедельную сводку из этих сигналов.
           Группируй по темам. Выдели топ-3 действия."
       │
       ▼
  Supabase Insert (digests)
       │
       ▼
  Telegram Bot: отправить пользователю сводку
```

---

## Чеклист готовности каждой фазы

### Фаза 1 ✅ если

- [ ] Supabase проект создан
- [ ] Все 4 таблицы существуют
- [ ] RLS включен
- [ ] Существующие данные мигрированы
- [ ] `curl` к API возвращает данные

### Фаза 2 ✅ если

- [ ] Telegram бот создан (@BotFather)
- [ ] n8n Cloud workflow работает
- [ ] Пересланное сообщение боту → появляется запись в `signals`
- [ ] AI правильно классифицирует (проверить 10 сообщений)
- [ ] Дубликаты не проходят

### Фаза 3 ✅ если

- [ ] RSS workflow запускается каждые 2 часа
- [ ] Новые статьи попадают в `signals` с корректным `relevance_score`
- [ ] Нерелевантные статьи (score < 40) не записываются

### Фаза 4 ✅ если

- [ ] Obsidian Vault содержит папку `MonitoringHub/`
- [ ] Новые сигналы (score ≥ 50) появляются как .md файлы
- [ ] Frontmatter корректен (теги, тема, route)
- [ ] Файлы попадают в правильные подпапки

### Фаза 5 ✅ если

- [ ] Дашборд загружает данные из Supabase
- [ ] Fallback на JSON работает при недоступности Supabase
- [ ] Realtime уведомления приходят при новом сигнале

### Фаза 6 ✅ если

- [ ] Запрос «что нового по RAG» → возвращает релевантные сигналы
- [ ] Embedding создаётся автоматически при INSERT
- [ ] API-ключ НЕ виден в клиентском коде

### Фаза 7 ✅ если

- [ ] Каждый понедельник приходит сводка в Telegram
- [ ] Сводка содержит топ-сигналы и 3 рекомендованных действия

---

## Файлы проекта (где что лежит)

```
c:\Users\Admin\.gemini\antigravity\scratch\Мой Дашборд\
  ├── index.html          ← дашборд (уже есть, модифицировать в Фазе 5)
  ├── app.js              ← логика дашборда (модифицировать в Фазе 5)
  ├── style.css           ← стили (не трогать)
  ├── data/
  │   ├── dashboard_data.json    ← исходные данные для миграции (Фаза 1)
  │   └── telegram_intelligence.json ← Telegram-источники для миграции
  ├── projects.json       ← проекты (мигрировать в Supabase)
  ├── scripts/
  │   └── sync_obsidian.py       ← [СОЗДАТЬ] скрипт синхронизации (Фаза 4)
  ├── docs/
  │   └── monitoring_hub_plan.md ← ЭТОТ ДОКУМЕНТ
  └── .env.example        ← [СОЗДАТЬ] шаблон переменных окружения
```

### .env.example

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GEMINI_API_KEY=AIza...
TELEGRAM_BOT_TOKEN=1234567890:ABC...
OBSIDIAN_VAULT_PATH=C:\Users\Admin\ObsidianVault
```

---

## Лимиты бесплатных тиров (следи за ними)

| Сервис | Лимит | Что будет если превысить |
|---|---|---|
| **n8n Cloud Free** | 5 workflows, 100 executions/день | Придётся перейти на VPS или n8n Starter ($20/мес) |
| **Supabase Free** | 500 МБ БД, 1 ГБ storage, 50K записей, 500K Edge Function вызовов/мес | Данные остаются, но write-операции блокируются |
| **Gemini API Free** | 15 RPM, 1M токенов/мин | Ошибка 429, нужно добавить retry с backoff |
| **GitHub Pages** | 1 ГБ, 100 ГБ bandwidth/мес | Достаточно для дашборда |

> [!IMPORTANT]
> **Когда переходить на VPS**: если n8n Cloud лимит (100 exec/день) станет узким местом. Тогда: `docker-compose up -d` на Hetzner CAX11 (€3.3/мес) — n8n + Supabase (self-hosted) на одном сервере. Docker-compose уже подготовлен в проекте.
