const { createClient } = require('@supabase/supabase-js');
const config = require('../config.js');

// Hack to load config.js which is meant for browser
global.window = { DASHBOARD_CONFIG: {} };
eval(require('fs').readFileSync('../config.js', 'utf8'));

const supabase = createClient(
    window.DASHBOARD_CONFIG.SUPABASE_URL,
    window.DASHBOARD_CONFIG.SUPABASE_KEY // using anon key for now, RLS allows insert
);

// We need service_role key to bypass RLS for robust seeding, 
// using anon key might fail if RLS prevents inserts for some reason.
// But let's try with anon key first since we added a permissive policy.

const relations = [
    { from_id: 'tgaggregator', to_id: 'knowledge-hub-unified', relation: 'part_of', note: 'Aggregator feeds Hub' },
    { from_id: 'interest-monitoring-loop', to_id: 'knowledge-hub-unified', relation: 'part_of', note: 'Loop feeds Hub' },
    { from_id: 'мой-дашборд', to_id: 'knowledge-hub-unified', relation: 'part_of', note: 'Dashboard visualizes Hub' },
    { from_id: 'самосовершенствующиеся-агенты', to_id: 'skills', relation: 'uses', note: 'Agents use skill modules' },
    { from_id: 'skills', to_id: 'ai-agent-core-workspace', relation: 'part_of', note: 'Skills live in core workspace' },
    { from_id: 'antigravity-dashboard-workspace', to_id: 'ai-agent-core-workspace', relation: 'part_of', note: null },
    { from_id: 'карта-технологий', to_id: 'skills', relation: 'spawned_from', note: 'Map inspired skill ideas' },
    { from_id: 'tech-radar-skill', to_id: 'skills', relation: 'spawned_from', note: 'Tech Radar → skill candidates' },
    { from_id: 'copaw-бот', to_id: 'tgaggregator', relation: 'uses', note: 'CoPaw sends signals to aggregator' },
    { from_id: 'генератор-идей', to_id: 'knowledge-hub-unified', relation: 'related', note: null },
    { from_id: 'ии-агент-для-гимназии', to_id: 'ai-agent-core-workspace', relation: 'uses', note: 'Gymnasium AI built on core stack' },
    { from_id: 'grant-presentation', to_id: 'ии-агент-для-гимназии', relation: 'related', note: 'Grant supports AI agent project' },
    { from_id: 'gymnasium-landing', to_id: 'ии-агент-для-гимназии', relation: 'related', note: null },
    { from_id: 'smartmeeting-backend', to_id: 'ai-agent-core-workspace', relation: 'uses', note: 'SmartMeeting is an agent skill' },
    { from_id: 'system-interest-map', to_id: 'interest-monitoring-loop', relation: 'spawned_from', note: 'System map grew from loop analysis' }
];

async function seedRelations() {
    console.log('Seeding project relations...');

    for (const rel of relations) {
        const { data, error } = await supabase
            .from('project_relations')
            .upsert(rel, { onConflict: 'from_id, to_id, relation' });

        if (error) {
            console.error(`Error inserting ${rel.from_id} -> ${rel.to_id}:`, error.message);
        } else {
            console.log(`✓ Inserted/Updated relation: ${rel.from_id} -> ${rel.to_id}`);
        }
    }

    console.log('Seed complete.');
}

seedRelations();
