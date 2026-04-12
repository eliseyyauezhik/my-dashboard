/**
 * migrate_knowledge.js
 * Milestone A: Enrich projects + insert ideas + goals into Supabase
 * 
 * Usage:
 *   1. First run migrate_schema.sql in Supabase SQL Editor
 *   2. Then: node scripts/migrate_knowledge.js
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Use service_role key for writes (only run locally, never in browser)
const SUPABASE_URL = 'https://szpwdhmayksqpppiqecn.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN6cHdkaG1heWtzcXBwcGlxZWNuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMzU5ODEsImV4cCI6MjA4ODkxMTk4MX0.8qg1kGUi8_NISGFek5RCX3jvStuIxez9gSjuXtCVwhM';

const sb = createClient(SUPABASE_URL, SUPABASE_KEY);

// Load projects.json
const dataPath = path.join(__dirname, '..', 'projects.json');
const data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));

// === Project group mapping ===
const projectGroups = data.projectGroups || data.monitoring?.projectGroups || [];

function buildGroupMap() {
    const map = {};
    for (const g of projectGroups) {
        for (const pid of g.projectIds) {
            map[pid] = { group_id: g.id, group_title: g.title };
        }
    }
    return map;
}

// === Life area mapping from ideas and monitoring profile ===
function buildLifeAreaMap() {
    const map = {};
    // From ideas
    for (const idea of (data.ideas || [])) {
        if (idea.relatedProjectId && idea.lifeArea) {
            map[idea.relatedProjectId] = idea.lifeArea;
        }
    }
    // Manual overrides based on project categories
    const categoryToArea = {
        'Образование': 'работа',
        'AI / Агенты': 'работа',
        'AI / Боты': 'работа',
        'Инфраструктура': 'работа',
        'Продукты': 'работа',
        'Бизнес': 'работа',
        'Продуктивность': 'я',
        'Личная система': 'я',
        'Медиа': 'я',
        'Гранты': 'работа',
    };
    return { map, categoryToArea };
}

async function enrichProjects() {
    console.log('\n=== Enriching projects ===');
    const groupMap = buildGroupMap();
    const { map: lifeAreaMap, categoryToArea } = buildLifeAreaMap();

    const { data: projects, error } = await sb.from('projects').select('id, title, category');
    if (error) { console.error('Error fetching projects:', error.message); return; }

    let updated = 0;
    for (const p of projects) {
        const group = groupMap[p.id] || {};
        const lifeArea = lifeAreaMap[p.id] || categoryToArea[p.category] || 'работа';

        const { error: ue } = await sb.from('projects').update({
            life_area: lifeArea,
            group_id: group.group_id || null,
            group_title: group.group_title || null,
        }).eq('id', p.id);

        if (ue) {
            console.error(`  ✗ ${p.title}: ${ue.message}`);
        } else {
            console.log(`  ✓ ${p.title} → area:${lifeArea}, group:${group.group_id || '—'}`);
            updated++;
        }
    }
    console.log(`Updated ${updated}/${projects.length} projects`);
}

async function insertIdeas() {
    console.log('\n=== Inserting ideas ===');
    const ideas = data.ideas || [];
    if (!ideas.length) { console.log('No ideas found in JSON'); return; }

    let inserted = 0;
    for (const idea of ideas) {
        const row = {
            id: idea.id,
            title: idea.title,
            description: idea.description,
            tags: idea.tags || [],
            priority: idea.priority || 'medium',
            life_area: idea.lifeArea || null,
            theme: idea.theme || null,
            theme_label: idea.themeLabel || null,
            route: idea.route || null,
            route_label: idea.routeLabel || null,
            related_project: idea.relatedProject || null,
            related_project_id: idea.relatedProjectId || null,
            relevance_score: idea.routingScore || 50,
            next_step: idea.routingNextStep || null,
            added_date: idea.addedDate || null,
            status: 'open',
        };

        const { error } = await sb.from('ideas').upsert(row, { onConflict: 'id' });
        if (error) {
            console.error(`  ✗ ${idea.title}: ${error.message}`);
        } else {
            console.log(`  ✓ ${idea.title} (${idea.priority})`);
            inserted++;
        }
    }
    console.log(`Inserted ${inserted}/${ideas.length} ideas`);
}

async function insertGoals() {
    console.log('\n=== Inserting goals ===');

    const goals = [
        {
            id: 'area-work',
            title: 'AI-проекты, образование, гранты, продуктовые и агентные системы',
            description: 'Разработка ИИ-решений для гимназии, развитие агентных навыков, грантовая деятельность и продуктовые запуски.',
            life_area: 'работа',
            status: 'active',
            focus_themes: ['AI-агенты и skills', 'образование и гранты', 'идеи -> проекты'],
            project_ids: [
                'tgaggregator', 'interest-monitoring-loop', 'мой-дашборд',
                'самосовершенствующиеся-агенты', 'grant-presentation',
                'gymnasium-landing', 'ии-агент-для-гимназии', 'knowledge-hub-unified'
            ],
        },
        {
            id: 'area-self',
            title: 'Личное развитие, инструменты, база знаний, планирование',
            description: 'Создание персональной инфраструктуры знаний: RAG-поиск, Obsidian, дашборд, навыки для агентов.',
            life_area: 'я',
            status: 'active',
            focus_themes: ['личная база знаний и RAG', 'AI-агенты и skills'],
            project_ids: [
                'карта-технологий', 'tech-radar-skill', 'skills',
                'system-interest-map', 'генератор-идей'
            ],
        },
        {
            id: 'area-family',
            title: 'Дом, дети, события, подарки, семейные решения',
            description: 'Семейная операционная система: планирование, события, координация.',
            life_area: 'семья',
            status: 'active',
            focus_themes: ['семейная операционная система'],
            project_ids: [],
        },
    ];

    let inserted = 0;
    for (const g of goals) {
        const { error } = await sb.from('goals').upsert(g, { onConflict: 'id' });
        if (error) {
            console.error(`  ✗ ${g.title}: ${error.message}`);
        } else {
            console.log(`  ✓ ${g.life_area}: ${g.title.substring(0, 50)}...`);
            inserted++;
        }
    }
    console.log(`Inserted ${inserted}/${goals.length} goals`);
}

async function verify() {
    console.log('\n=== Verification ===');

    const { data: projects } = await sb.from('projects').select('id, group_id, life_area').not('group_id', 'is', null);
    console.log(`Projects with group_id: ${projects?.length || 0}`);

    const { data: ideas, count: ic } = await sb.from('ideas').select('*', { count: 'exact' });
    console.log(`Ideas: ${ic || ideas?.length || 0}`);

    const { data: goals, count: gc } = await sb.from('goals').select('*', { count: 'exact' });
    console.log(`Goals: ${gc || goals?.length || 0}`);

    const { data: notes, count: nc } = await sb.from('notes').select('*', { count: 'exact' });
    console.log(`Notes: ${nc || notes?.length || 0} (empty for now, will grow from signals)`);
}

async function main() {
    console.log('🚀 Knowledge Base Migration — Milestone A');
    console.log('==========================================');

    await enrichProjects();
    await insertIdeas();
    await insertGoals();
    await verify();

    console.log('\n✅ Migration complete!');
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
