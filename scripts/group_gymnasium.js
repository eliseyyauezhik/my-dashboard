const { createClient } = require('@supabase/supabase-js');

// Hack to load config.js which is meant for browser
global.window = { DASHBOARD_CONFIG: {} };
eval(require('fs').readFileSync('config.js', 'utf8'));

const supabase = createClient(
    window.DASHBOARD_CONFIG.SUPABASE_URL,
    window.DASHBOARD_CONFIG.SUPABASE_KEY
);

async function groupGymnasiumProjects() {
    console.log('Fetching projects...');
    const { data: projects, error } = await supabase.from('projects').select('id, title, group_id');
    if (error) {
        console.error("Error fetching projects:", error);
        return;
    }

    // Keywords to find gymnasium projects
    const keywords = ['гимнази', 'gymnasium', 'газета', 'davydov'];

    const targetGroupId = 'gymnasium-projects';
    const targetGroupTitle = 'Гимназия им. В.В. Давыдова';

    let toUpdate = [];

    console.log('--- Current Projects ---');
    projects.forEach(p => {
        const titleLower = p.title.toLowerCase();
        const isMatch = keywords.some(k => titleLower.includes(k)) ||
            (p.group_id && p.group_id.includes('gymnasi'));

        if (isMatch) {
            console.log(`- Match found: [${p.id}] ${p.title} (Current group: ${p.group_id})`);
            if (p.group_id !== targetGroupId) {
                toUpdate.push(p.id);
            }
        }
    });

    if (toUpdate.length === 0) {
        console.log('\nNo projects need updating.');
        return;
    }

    console.log(`\nUpdating ${toUpdate.length} projects to group '${targetGroupId}'...`);

    for (const id of toUpdate) {
        const { error: updateError } = await supabase
            .from('projects')
            .update({ group_id: targetGroupId, group_title: targetGroupTitle })
            .eq('id', id);

        if (updateError) {
            console.error(`Error updating project ${id}:`, updateError.message);
        } else {
            console.log(`✓ Updated ${id}`);
        }
    }
}

groupGymnasiumProjects();
