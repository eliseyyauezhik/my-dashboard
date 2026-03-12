const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// 1. Читаем ключи из кастомного файла .env/supabase API.env
const envPath = path.join(__dirname, '..', '.env', 'supabase API.env');
const envContent = fs.readFileSync(envPath, 'utf8').split('\n');
const supabaseUrl = envContent[0].trim();
const supabaseKey = envContent[1].trim();

console.log('🔗 URL:', supabaseUrl);
console.log('🔑 Key len:', supabaseKey.length);

const supabase = createClient(supabaseUrl, supabaseKey);

async function migrate() {
    console.log('🚀 Начинаем миграцию...');

    // 2. Читаем данные проектов
    const dashboardDataPath = path.join(__dirname, '..', 'data', 'dashboard_data.json');
    const dbData = JSON.parse(fs.readFileSync(dashboardDataPath, 'utf8'));

    const projects = dbData.projects.map(p => ({
        id: p.id,
        title: p.title,
        description: p.description,
        status: p.status || 'active',
        category: p.category || '',
        tags: p.tags || [],
        progress: p.progress || 0,
        updated_at: p.lastUpdated ? new Date(p.lastUpdated).toISOString() : new Date().toISOString()
    }));

    console.log(`📦 Подготовлено проектов: ${projects.length}`);

    // Отправляем проекты в Supabase
    const { data: pData, error: pError } = await supabase
        .from('projects')
        .upsert(projects, { onConflict: 'id' });

    if (pError) {
        console.error('❌ Ошибка миграции проектов:', pError);
    } else {
        console.log('✅ Проекты успешно загружены!');
    }

    // 3. Читаем источники из Telegram Intelligence (если файл есть)
    const intelPath = path.join(__dirname, '..', 'data', 'telegram_intelligence.json');
    if (fs.existsSync(intelPath)) {
        const intelData = JSON.parse(fs.readFileSync(intelPath, 'utf8'));
        const sources = intelData.sources || [];

        const mappedSources = sources.map(s => ({
            title: s.name || s.title || 'Unknown',
            type: s.type === 'channel' ? 'telegram_channel' : (s.type === 'chat' ? 'telegram_chat' : 'manual'),
            url: s.url || '',
            is_active: true
        }));

        if (mappedSources.length > 0) {
            console.log(`📡 Подготовлено источников: ${mappedSources.length}`);
            const { data: sData, error: sError } = await supabase
                .from('sources')
                .insert(mappedSources);

            if (sError) {
                console.error('❌ Ошибка миграции источников:', sError);
            } else {
                console.log('✅ Источники успешно загружены!');
            }
        }
    } else {
        console.log('ℹ️ Файл telegram_intelligence.json не найден, пропускаем источники.');
    }

    console.log('🎉 Миграция завершена!');
}

migrate();
