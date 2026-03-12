import json
import sys

# We'll use dashboard_data.json because it contains all unified project data
try:
    with open('c:/Users/Admin/.gemini/antigravity/scratch/Мой Дашборд/data/dashboard_data.json', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    print("Error reading file:", e)
    sys.exit(1)

target_ids = ['tgaggregator', 'interest-monitoring-loop', 'мой-дашборд', 'copaw-бот', 'генератор-идей', 'appscout', 'карта-технологий', 'system-interest-map']
print("=== ПРОЕКТЫ ПО ПОИСКУ И МОНИТОРИНГУ ===")
for p in data.get('projects', []):
    pid = p.get('id', '')
    title = p.get('title', '')
    desc = p.get('description', '')
    status = p.get('status', '')
    
    # We also check if the system group "news-aggregators" or "idea-generators" or "ai-system-growth"
    if pid in target_ids:
        print(f"\n{title} ({status})")
        print(f"Описание: {desc}")
