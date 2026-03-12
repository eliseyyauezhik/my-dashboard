import json
import io
import sys

# We'll use dashboard_data.json because it contains all unified project data
try:
    with open('c:/Users/Admin/.gemini/antigravity/scratch/Мой Дашборд/data/dashboard_data.json', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print("Error reading file:", e)
    sys.exit(1)

target_ids = ['tgaggregator', 'interest-monitoring-loop', 'мой-дашборд', 'copaw-бот', 'генератор-идей', 'appscout', 'карта-технологий', 'system-interest-map']
with io.open('c:/Users/Admin/.gemini/antigravity/scratch/Мой Дашборд/tmp_monitoring.txt', mode='w', encoding='utf-8') as f:
    f.write("=== ПРОЕКТЫ ПО ПОИСКУ И МОНИТОРИНГУ ===\n")
    for p in data.get('projects', []):
        pid = p.get('id', '')
        title = p.get('title', '')
        desc = p.get('description', '')
        status = p.get('status', '')
        
        # We also check if the system group "news-aggregators" or "idea-generators" or "ai-system-growth"
        if pid in target_ids:
            f.write(f"\n{title} ({status})\n")
            f.write(f"Описание: {desc}\n")
