import json
import os

data_path = "c:/Users/Admin/.gemini/antigravity/scratch/Мой Дашборд/data/dashboard_data.json"
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

hub_id = "knowledge-hub-unified"
hub_found = False
for p in data["projects"]:
    if p.get("id") == hub_id:
        hub_found = True
        p["description"] = "Единый центр (n8n + Supabase + VPS + Obsidian) для сбора, обработки и поиска информации."
        p["tasks"] = {
            "todo": ["Арендовать VPS для n8n + БД", "Настроить Webhook из Telegram в n8n"],
            "done": ["Спроектировать архитектуру (MVP v3.0)", "Подготовить docker-compose.yml для VPS"]
        }
        break

if not hub_found:
    new_project = {
        "id": hub_id,
        "title": "Умный Хаб Знаний (Monitoring Hub)",
        "description": "Единый центр (n8n + Supabase + VPS + Obsidian) для сбора, обработки и поиска информации.",
        "status": "active",
        "topic": "antigravity",
        "tags": ["AI", "Knowledge Base", "VPS", "n8n", "RAG"],
        "tasks": {
            "todo": ["Арендовать VPS для n8n + БД", "Настроить Webhook из Telegram в n8n"],
            "done": ["Спроектировать архитектуру (MVP v3.0)", "Подготовить docker-compose.yml для VPS"]
        }
    }
    data["projects"].insert(0, new_project)

backup_path = data_path + ".bak"
os.rename(data_path, backup_path)
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Dashboard data updated with unified project and tasks.")
