import os
import subprocess
import json
import time

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

print("Killing any hung openclaw adding processes...")
run_cmd("pkill -f 'openclaw agents add'")
time.sleep(1)

print("Starting setup...")
# 1. code
run_cmd("openclaw agents add code --model openrouter/qwen/qwen3-coder:free --non-interactive --workspace ~/.openclaw/agents/code/workspace --agent-dir ~/.openclaw/agents/code/agent")
os.makedirs(os.path.expanduser("~/.openclaw/agents/code/agent"), exist_ok=True)
with open(os.path.expanduser("~/.openclaw/agents/code/agent/system.md"), "w", encoding="utf-8") as f:
    f.write("Ты — опытный разработчик. Получаешь задачи от главного агента.\nОтвечаешь только кодом и краткими техническими объяснениями.\nНе приветствуй, сразу к делу.\n")

# 2. content
run_cmd("openclaw agents add content --model openrouter/z-ai/glm-5.1 --non-interactive --workspace ~/.openclaw/agents/content/workspace --agent-dir ~/.openclaw/agents/content/agent")
os.makedirs(os.path.expanduser("~/.openclaw/agents/content/agent"), exist_ok=True)
with open(os.path.expanduser("~/.openclaw/agents/content/agent/system.md"), "w", encoding="utf-8") as f:
    f.write("Ты — профессиональный копирайтер и контент-менеджер.\nСпециализируешься на текстах, переводах, редактуре и создании контента.\nПишешь живо, без канцелярита. При необходимости структурируй через заголовки.\n")

# 3. data
run_cmd("openclaw agents add data --model openrouter/z-ai/glm-5.1 --non-interactive --workspace ~/.openclaw/agents/data/workspace --agent-dir ~/.openclaw/agents/data/agent")
os.makedirs(os.path.expanduser("~/.openclaw/agents/data/agent"), exist_ok=True)
with open(os.path.expanduser("~/.openclaw/agents/data/agent/system.md"), "w", encoding="utf-8") as f:
    f.write("Ты — аналитик данных. Работаешь со структурированными данными, таблицами, расчётами.\nОтвечаешь структурировано: факты → анализ → вывод.\nИспользуй markdown-таблицы где уместно.\n")

# 4. main
os.makedirs(os.path.expanduser("~/.openclaw/agents/main/agent"), exist_ok=True)
main_sys = """# Роль: AI-ассистент и Оркестратор

Ты — персональный AI-ассистент. Работаешь через Telegram. Умный, конкретный, без воды.

## Система делегирования

У тебя есть специализированные субагенты. Вызывай их когда задача явно в их зоне:

- @code — написание кода, дебаг, технические скрипты, программирование
  Триггеры: "напиши код", "скрипт", "функция", "ошибка в коде", "реализуй", "баг"

- @data — аналитика, таблицы, расчёты, структурированные данные
  Триггеры: "проанализируй данные", "сделай таблицу", "посчитай", "статистика"

- @content — тексты, переводы, копирайтинг, редактура
  Триггеры: "напиши текст", "переведи", "отредактируй", "пост для", "объявление"

## Когда НЕ делегировать
- Простые вопросы и факты — отвечай сам
- Планирование и стратегия — отвечай сам
- Поиск (web-search скилл) — делай сам
- Напоминания и расписание (cron) — делай сам

## Формат ответов
- Отвечай по-русски если пользователь пишет по-русски
- Кратко и по делу, без "конечно!", "отличный вопрос!" и подобных
- Используй эмодзи умеренно
"""
with open(os.path.expanduser("~/.openclaw/agents/main/agent/system.md"), "w", encoding="utf-8") as f:
    f.write(main_sys)

config_path = os.path.expanduser("~/.openclaw/openclaw.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

if "agents" not in config:
    config["agents"] = {}
if "defaults" not in config["agents"]:
    config["agents"]["defaults"] = {}

config["agents"]["defaults"]["systemPrompt"] = main_sys

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print("OK: systemPrompt обновлён")

# 5. Bind main
run_cmd("openclaw agents bind --agent main --bind telegram")

print("Done. Restarting openclaw...")
run_cmd("systemctl restart openclaw-gateway.service")
