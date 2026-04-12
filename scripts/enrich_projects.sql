-- =============================================================
-- Enrich projects with life_area, group_id, group_title
-- Run this in Supabase SQL Editor
-- =============================================================

-- Group: Агрегаторы новостей и мониторинг (news-aggregators)
UPDATE projects SET group_id = 'news-aggregators', group_title = 'Агрегаторы новостей и мониторинг', life_area = 'работа' WHERE id = 'tgaggregator';
UPDATE projects SET group_id = 'news-aggregators', group_title = 'Агрегаторы новостей и мониторинг', life_area = 'я' WHERE id = 'interest-monitoring-loop';
UPDATE projects SET group_id = 'news-aggregators', group_title = 'Агрегаторы новостей и мониторинг', life_area = 'работа' WHERE id = 'мой-дашборд';
UPDATE projects SET group_id = 'news-aggregators', group_title = 'Агрегаторы новостей и мониторинг', life_area = 'работа' WHERE id = 'copaw-бот';
UPDATE projects SET group_id = 'news-aggregators', group_title = 'Агрегаторы новостей и мониторинг', life_area = 'семья' WHERE id = 'генератор-идей';

-- Group: Генераторы идей и визуализация (idea-generators)
UPDATE projects SET group_id = 'idea-generators', group_title = 'Генераторы идей и визуализация', life_area = 'работа' WHERE id = 'карта-технологий';
UPDATE projects SET group_id = 'idea-generators', group_title = 'Генераторы идей и визуализация', life_area = 'работа' WHERE id = 'tech-radar-skill';

-- Group: Развитие ИИ-системы (ai-system-growth)
UPDATE projects SET group_id = 'ai-system-growth', group_title = 'Развитие ИИ-системы (ядро/база знаний)', life_area = 'работа' WHERE id = 'appscout';
UPDATE projects SET group_id = 'ai-system-growth', group_title = 'Развитие ИИ-системы (ядро/база знаний)', life_area = 'работа' WHERE id = 'ai-agent-core-workspace';
UPDATE projects SET group_id = 'ai-system-growth', group_title = 'Развитие ИИ-системы (ядро/база знаний)', life_area = 'работа' WHERE id = 'antigravity-dashboard-workspace';
UPDATE projects SET group_id = 'ai-system-growth', group_title = 'Развитие ИИ-системы (ядро/база знаний)', life_area = 'я' WHERE id = 'system-interest-map';

-- Group: ИИ-агенты и автоматизация (ai-agents)
UPDATE projects SET group_id = 'ai-agents', group_title = 'ИИ-агенты и автоматизация', life_area = 'работа' WHERE id = 'самосовершенствующиеся-агенты';
UPDATE projects SET group_id = 'ai-agents', group_title = 'ИИ-агенты и автоматизация', life_area = 'работа' WHERE id = 'skills';

-- Group: Рабочие проекты - Гимназия/Бизнес (work-projects)
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'davydov-phantom';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'grant-presentation';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'gymnasium-landing';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'interactive-panels-rating';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'smartmeeting-backend';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'kora-strategy';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'ии-агент-для-гимназии';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'я' WHERE id = 'видео-для-гранта';
UPDATE projects SET group_id = 'work-projects', group_title = 'Рабочие проекты (Гимназия/Бизнес)', life_area = 'работа' WHERE id = 'презентация-образование-2035';

-- Ungrouped project
UPDATE projects SET life_area = 'работа' WHERE id = 'knowledge-hub-unified';

SELECT id, title, life_area, group_id FROM projects ORDER BY group_id;
