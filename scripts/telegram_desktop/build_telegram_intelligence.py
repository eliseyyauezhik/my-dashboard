#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


DEFAULT_EXPORTS_ROOT = Path(r"C:\Users\Kogan\Downloads\Telegram Desktop")
DEFAULT_DASHBOARD_DATA = Path("data/dashboard_data.json")
DEFAULT_TOPICS_JSON = Path(r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase\Config\topics.json")
DEFAULT_OBSIDIAN_ROOT = Path(r"D:\ЯндексДиск\Yandex.Disk\ПРОЕКТЫ\KnowledgeBase")
DEFAULT_OUT_JSON = Path("data/telegram_intelligence.json")

SOURCE_NOTES_DIR = Path("Inbox/Telegram Desktop Intelligence/Sources")
SOURCE_SUMMARY_NOTE = Path("Inbox/Telegram Desktop Intelligence/00_INDEX.md")
SOURCE_OVERVIEW_NOTE = Path("Dashboards/Telegram Desktop Intelligence.md")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "бы",
    "будет",
    "быть",
    "вам",
    "вас",
    "ваш",
    "ваша",
    "ваши",
    "все",
    "всё",
    "вот",
    "вы",
    "где",
    "да",
    "даже",
    "для",
    "до",
    "его",
    "ее",
    "её",
    "если",
    "есть",
    "еще",
    "ещё",
    "же",
    "за",
    "из",
    "или",
    "им",
    "их",
    "кто",
    "как",
    "ко",
    "когда",
    "который",
    "ли",
    "либо",
    "меня",
    "много",
    "мне",
    "можно",
    "может",
    "мой",
    "моя",
    "мы",
    "на",
    "не",
    "него",
    "нее",
    "неё",
    "нет",
    "но",
    "ну",
    "нужно",
    "них",
    "о",
    "об",
    "один",
    "он",
    "она",
    "они",
    "оно",
    "от",
    "по",
    "под",
    "при",
    "просто",
    "про",
    "с",
    "со",
    "себе",
    "себя",
    "сейчас",
    "так",
    "там",
    "те",
    "то",
    "только",
    "тут",
    "ты",
    "у",
    "уже",
    "хотя",
    "чем",
    "что",
    "чтобы",
    "это",
    "этот",
    "эта",
    "эти",
    "я",
}

TITLE_THEME_HINTS = {
    "план": ("я", "planning"),
    "saved messages": ("я", "inbox"),
    "saved_messages": ("я", "inbox"),
    "мой бизнес": ("работа", "business"),
    "работа": ("работа", "operations"),
    "проекты для гимназии давыдова": ("работа", "education"),
    "развитие гимназии давыдова": ("работа", "education"),
    "учеба": ("я", "learning"),
    "учеба ": ("я", "learning"),
    "боты": ("я", "ai-tools"),
    "иишенка": ("работа", "ai-tools"),
    "никита велс": ("работа", "ai-business"),
    "дрессировщик нейросетей": ("работа", "ai-tools"),
    "web3nity": ("работа", "community"),
    "кора 35 лет": ("работа", "events"),
    "дети": ("семья", "family"),
    "мой дом": ("семья", "home"),
    "подарки": ("семья", "family"),
    "новый год коганы": ("семья", "family"),
    "др елисея": ("семья", "family"),
    "новая жизнь": ("я", "self-development"),
    "3д принтер": ("я", "maker"),
}

THEME_KEYWORDS = {
    "ai-tools": {
        "agents",
        "ai",
        "bot",
        "bots",
        "chatgpt",
        "claude",
        "gpt",
        "нейросет",
        "промпт",
        "prompt",
        "автоматизац",
        "агент",
        "бот",
        "ии",
        "скилл",
        "skill",
        "workflow",
    },
    "ai-business": {
        "ai",
        "automation",
        "business",
        "content",
        "growth",
        "marketing",
        "sales",
        "wb",
        "wildberries",
        "бизнес",
        "контент",
        "маркетинг",
        "продажи",
        "упаковк",
        "ии",
        "автоматизац",
    },
    "education": {
        "grant",
        "school",
        "гимназ",
        "грант",
        "дети",
        "образован",
        "учеб",
        "школ",
    },
    "inbox": {
        "bookmark",
        "idea",
        "inbox",
        "link",
        "save",
        "saved",
        "заметк",
        "идея",
        "сохран",
        "ссылка",
    },
    "planning": {
        "goal",
        "plan",
        "задач",
        "план",
        "приоритет",
        "цель",
    },
    "home": {
        "дом",
        "ремонт",
        "home",
        "быт",
        "интерьер",
    },
    "family": {
        "дети",
        "подар",
        "празд",
        "семь",
        "елисе",
        "новый",
    },
    "maker": {
        "3д",
        "3d",
        "print",
        "printer",
        "печат",
        "принтер",
    },
    "self-development": {
        "growth",
        "habit",
        "life",
        "mindset",
        "новая",
        "привыч",
        "развити",
        "жизн",
    },
    "events": {
        "event",
        "празд",
        "событ",
        "юбилей",
        "кора",
    },
    "community": {
        "chat",
        "community",
        "crypto",
        "web3",
        "web3nity",
        "крипт",
        "сообществ",
    },
    "operations": {
        "операц",
        "работ",
        "процесс",
        "заказ",
        "команд",
    },
}

THEME_TO_AREA = {
    "ai-tools": "работа",
    "ai-business": "работа",
    "business": "работа",
    "education": "работа",
    "events": "работа",
    "community": "работа",
    "operations": "работа",
    "inbox": "я",
    "learning": "я",
    "planning": "я",
    "self-development": "я",
    "maker": "я",
    "family": "семья",
    "home": "семья",
}

THEME_LABELS = {
    "ai-tools": "AI и инструменты",
    "ai-business": "AI в бизнесе",
    "education": "Образование и гранты",
    "inbox": "Идеи и архив",
    "planning": "Планирование",
    "home": "Дом",
    "family": "Семья и события",
    "maker": "3D и мейкерство",
    "self-development": "Саморазвитие",
    "events": "События и комьюнити",
    "community": "Сообщества",
    "operations": "Операционка",
    "mixed": "Смешанная тема",
    "business": "Бизнес",
    "learning": "Обучение",
}

AREA_LABELS = {
    "я": "Я",
    "семья": "Семья",
    "работа": "Работа",
}

RU_MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}


@dataclass
class ExportDigest:
    source_key: str
    source_id: str
    title: str
    source_type: str
    export_format: str
    export_dir: Path
    primary_file: Path
    message_count: int
    valid: bool
    parse_status: str
    first_date: str
    last_date: str
    token_counter: Counter[str]
    links: Counter[str]
    mentions: Counter[str]
    hashtags: Counter[str]
    sample_messages: list[str]
    media_count: int
    file_count: int
    sender_counter: Counter[str]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(value: str, fallback: str = "item") -> str:
    text = value.strip().lower()
    text = re.sub(r"[^\wа-яё]+", "-", text, flags=re.IGNORECASE)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or fallback


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def tokenise(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9][a-zA-Zа-яА-ЯёЁ0-9_-]{1,}", text.lower())
    cleaned: list[str] = []
    for token in tokens:
        if token in STOPWORDS:
            continue
        if token.isdigit():
            continue
        if not re.search(r"[a-zа-яё]", token):
            continue
        if re.fullmatch(r"[0-9a-f]{2,}", token):
            continue
        cleaned.append(token)
    return cleaned


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        if "text" in value:
            return flatten_text(value.get("text"))
        return ""
    return str(value)


def parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def date_label(value: str | None) -> str:
    dt = parse_iso_date(value)
    if not dt:
        return "—"
    return f"{dt.day} {RU_MONTHS[dt.month]} {dt.year}"


def short_text(value: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def html_to_text(value: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_result_json(path: Path) -> ExportDigest:
    source_type = "unknown"
    title = path.parent.name
    source_id = slugify(title)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        title = str(payload.get("name") or payload.get("title") or title).strip() or title
        source_type = str(payload.get("type") or "unknown")
        source_id = str(payload.get("id") or slugify(title))
        if source_type == "saved_messages" and title == path.parent.name:
            title = "Saved Messages"
        messages = payload.get("messages") or []
        token_counter: Counter[str] = Counter()
        links: Counter[str] = Counter()
        mentions: Counter[str] = Counter()
        hashtags: Counter[str] = Counter()
        sender_counter: Counter[str] = Counter()
        sample_messages: list[str] = []
        media_count = 0
        file_count = 0
        first_date = ""
        last_date = ""

        for message in messages:
            if not isinstance(message, dict):
                continue
            when = str(message.get("date") or "")
            if when:
                if not first_date:
                    first_date = when
                last_date = when

            sender = str(message.get("from") or message.get("actor") or "").strip()
            if sender:
                sender_counter[sender] += 1

            flat = flatten_text(message.get("text"))
            if flat:
                token_counter.update(tokenise(flat))
                for url in re.findall(r"https?://[^\s]+", flat):
                    links[url] += 1
                for mention in re.findall(r"(?<!\w)@[\w\d_]+", flat):
                    mentions[mention.lower()] += 1
                for tag in re.findall(r"(?<!\w)#[\w\d_]+", flat):
                    hashtags[tag.lower()] += 1
                if len(sample_messages) < 8 and len(flat.strip()) >= 80:
                    sample_messages.append(short_text(flat.strip(), limit=180))

            for entity in message.get("text_entities") or []:
                if not isinstance(entity, dict):
                    continue
                kind = str(entity.get("type") or "")
                entity_text = str(entity.get("text") or entity.get("href") or "")
                if kind in {"link", "text_link"} and entity_text:
                    links[entity_text] += 1
                if kind == "mention" and entity_text:
                    mentions[entity_text.lower()] += 1
                if kind == "hashtag" and entity_text:
                    hashtags[entity_text.lower()] += 1

            if message.get("photo") or message.get("thumbnail") or message.get("sticker_emoji"):
                media_count += 1
            if message.get("file") or message.get("file_name") or message.get("mime_type"):
                file_count += 1

        return ExportDigest(
            source_key=str(source_id),
            source_id=str(source_id),
            title=title,
            source_type=source_type,
            export_format="json",
            export_dir=path.parent,
            primary_file=path,
            message_count=len(messages),
            valid=True,
            parse_status="ok",
            first_date=first_date,
            last_date=last_date,
            token_counter=token_counter,
            links=links,
            mentions=mentions,
            hashtags=hashtags,
            sample_messages=sample_messages,
            media_count=media_count,
            file_count=file_count,
            sender_counter=sender_counter,
        )
    except Exception:
        raw = path.read_text(encoding="utf-8", errors="replace")
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
        type_match = re.search(r'"type"\s*:\s*"([^"]+)"', raw)
        id_match = re.search(r'"id"\s*:\s*([0-9]+)', raw)
        date_matches = re.findall(r'"date"\s*:\s*"([^"]+)"', raw)
        text_bits = [html.unescape(x) for x in re.findall(r'"text"\s*:\s*"([^"]{20,600})"', raw)]
        token_counter: Counter[str] = Counter()
        links: Counter[str] = Counter(re.findall(r"https?://[^\s\"\\]+", raw))
        mentions: Counter[str] = Counter(m.lower() for m in re.findall(r"(?<!\w)@[\w\d_]+", raw))
        hashtags: Counter[str] = Counter(t.lower() for t in re.findall(r"(?<!\w)#[\w\d_]+", raw))
        for bit in text_bits[:300]:
            token_counter.update(tokenise(bit))
        sample_messages = [short_text(x, 180) for x in text_bits[:6]]
        return ExportDigest(
            source_key=str(id_match.group(1) if id_match else slugify(name_match.group(1) if name_match else title)),
            source_id=str(id_match.group(1) if id_match else slugify(name_match.group(1) if name_match else title)),
            title=(name_match.group(1) if name_match else title).strip(),
            source_type=type_match.group(1) if type_match else "unknown",
            export_format="json",
            export_dir=path.parent,
            primary_file=path,
            message_count=max(len(re.findall(r'"type"\s*:\s*"message"', raw)), len(text_bits)),
            valid=False,
            parse_status="json_fallback",
            first_date=date_matches[0] if date_matches else "",
            last_date=date_matches[-1] if date_matches else "",
            token_counter=token_counter,
            links=links,
            mentions=mentions,
            hashtags=hashtags,
            sample_messages=sample_messages,
            media_count=len(re.findall(r'"photo"\s*:', raw)),
            file_count=len(re.findall(r'"file"\s*:', raw)),
            sender_counter=Counter(),
        )


def parse_html_export(path: Path) -> ExportDigest:
    raw = path.read_text(encoding="utf-8", errors="replace")
    title_match = re.search(r'<div class="text bold">\s*(.*?)\s*</div>', raw, flags=re.IGNORECASE | re.DOTALL)
    title = html_to_text(title_match.group(1)) if title_match else path.parent.name
    message_blocks = re.findall(r'<div class="text">\s*(.*?)\s*</div>', raw, flags=re.IGNORECASE | re.DOTALL)
    texts = [html_to_text(block) for block in message_blocks if html_to_text(block)]
    token_counter: Counter[str] = Counter()
    links: Counter[str] = Counter()
    mentions: Counter[str] = Counter()
    hashtags: Counter[str] = Counter()
    for text in texts:
        token_counter.update(tokenise(text))
        for url in re.findall(r"https?://[^\s]+", text):
            links[url] += 1
        for mention in re.findall(r"(?<!\w)@[\w\d_]+", text):
            mentions[mention.lower()] += 1
        for tag in re.findall(r"(?<!\w)#[\w\d_]+", text):
            hashtags[tag.lower()] += 1

    title_attrs = re.findall(r'title="([0-9.:\sUTC+-]+)"', raw, flags=re.IGNORECASE)
    dates = []
    for item in title_attrs:
        clean = html.unescape(item).replace(" UTC+03:00", "").strip()
        dt = parse_iso_date(clean)
        if dt:
            dates.append(dt.strftime("%Y-%m-%dT%H:%M:%S"))

    return ExportDigest(
        source_key=slugify(title),
        source_id=slugify(title),
        title=title,
        source_type="html_export",
        export_format="html",
        export_dir=path.parent,
        primary_file=path,
        message_count=len(texts),
        valid=True,
        parse_status="ok",
        first_date=dates[0] if dates else "",
        last_date=dates[-1] if dates else "",
        token_counter=token_counter,
        links=links,
        mentions=mentions,
        hashtags=hashtags,
        sample_messages=[short_text(x, 180) for x in texts[:8]],
        media_count=len(re.findall(r'class="media clearfix', raw)),
        file_count=len(re.findall(r'class="media_file', raw)),
        sender_counter=Counter(),
    )


def load_dashboard_context(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"projects": [], "workflows": [], "chats": [], "stats": {}, "meta": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def load_topics(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("topics") or []


def project_tokens(project: dict[str, Any]) -> set[str]:
    parts = [
        str(project.get("title") or ""),
        str(project.get("description") or ""),
        str(project.get("topic") or ""),
        " ".join(project.get("tags") or []),
    ]
    return set(tokenise(" ".join(parts)))


def theme_from_digest(title: str, tokens: list[str]) -> str:
    normalized = normalize_title(title)
    for hint, (_, theme) in TITLE_THEME_HINTS.items():
        if hint in normalized:
            return theme
    scores: Counter[str] = Counter()
    token_set = set(tokens)
    for theme, words in THEME_KEYWORDS.items():
        scores[theme] += len(token_set & words)
        for token in token_set:
            if any(token.startswith(word) for word in words):
                scores[theme] += 1
    theme, score = scores.most_common(1)[0] if scores else ("mixed", 0)
    return theme if score > 0 else "mixed"


def area_from_title_theme(title: str, theme: str) -> str:
    normalized = normalize_title(title)
    for hint, (area, _) in TITLE_THEME_HINTS.items():
        if hint in normalized:
            return area
    return THEME_TO_AREA.get(theme, "работа")


def format_top_entries(counter: Counter[str], limit: int = 6) -> list[str]:
    return [item for item, _ in counter.most_common(limit)]


def determine_application_principles(title: str, theme: str, digest: ExportDigest, related_projects: list[dict[str, Any]]) -> list[str]:
    principles: list[str] = []
    normalized = normalize_title(title)
    if digest.links:
        principles.append("Выделять ссылки и превращать их в короткие action-notes, а не хранить весь поток как ленту.")
    if digest.message_count >= 200:
        principles.append("Смотреть источник как устойчивый тематический поток: разбирать пакетно раз в неделю, а не читать хаотично.")
    if "saved_messages" in normalized or theme == "inbox":
        principles.append("Использовать как личный inbox: каждый входящий элемент должен стать либо задачей, либо заметкой, либо архивом.")
    if theme in {"family", "home"}:
        principles.append("Переводить обсуждения в чек-листы, события календаря и семейные решения с дедлайнами.")
    if theme in {"ai-tools", "ai-business"}:
        principles.append("Сжимать в reusable-формат: инструмент, кейс, принцип применения, ограничения, следующий эксперимент.")
    if theme == "education":
        principles.append("Связывать идеи с уже идущими образовательными проектами и грантовой повесткой, иначе знания не капитализируются.")
    if related_projects:
        principles.append("Проверять связь с действующими проектами до создания новых сущностей, чтобы не размножать параллельные ветки.")
    if not principles:
        principles.append("Сначала извлекать суть и тегировать, потом решать: проект, задача, reference или архив.")
    return principles[:4]


def summarize_source(title: str, theme: str, digest: ExportDigest, related_projects: list[dict[str, Any]]) -> str:
    theme_label = THEME_LABELS.get(theme, "Смешанная тема")
    top_keywords = format_top_entries(digest.token_counter, limit=5)
    keywords_part = ", ".join(top_keywords) if top_keywords else "явные маркеры не выделены"
    project_part = ""
    if related_projects:
        project_part = " Связано с проектами: " + ", ".join(p["title"] for p in related_projects[:3]) + "."
    return (
        f"{title} — источник по теме «{theme_label}» с {digest.message_count} сообщениями "
        f"({date_label(digest.first_date)} — {date_label(digest.last_date)}). "
        f"Сигнальные слова: {keywords_part}.{project_part}"
    )


def compute_rank_score(
    digest: ExportDigest,
    theme: str,
    related_projects_count: int,
    topic_matches_count: int,
    today_value: date,
) -> int:
    msg_score = min(32.0, math.log10(digest.message_count + 1) * 10.0)
    link_score = min(12.0, math.log10(sum(digest.links.values()) + 1) * 6.0)
    mention_score = min(8.0, math.log10(sum(digest.mentions.values()) + 1) * 5.0)
    attachment_score = min(8.0, math.log10(digest.media_count + digest.file_count + 1) * 4.0)
    project_score = min(16.0, related_projects_count * 4.0)
    topic_score = min(12.0, topic_matches_count * 4.0)
    recency_score = 0.0
    last_dt = parse_iso_date(digest.last_date)
    if last_dt:
        age_days = max(0, (today_value - last_dt.date()).days)
        recency_score = max(0.0, 18.0 - min(age_days, 540) / 30.0)
    format_score = 4.0 if digest.valid else 2.0
    theme_bonus = 6.0 if theme in {"ai-tools", "ai-business", "education", "inbox"} else 3.0
    score = msg_score + link_score + mention_score + attachment_score + project_score + topic_score + recency_score + format_score + theme_bonus
    return max(1, min(100, int(round(score))))


def extract_domains(counter: Counter[str], limit: int = 5) -> list[str]:
    domains: Counter[str] = Counter()
    for url, count in counter.items():
        match = re.search(r"https?://([^/]+)", url)
        if match:
            domains[match.group(1).lower()] += count
    return [item for item, _ in domains.most_common(limit)]


def build_skill_suggestions(source_rows: list[dict[str, Any]], dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    themes = Counter(row["theme"] for row in source_rows)
    source_titles = {row["title"].lower(): row for row in source_rows}
    active_project_titles = [p.get("title") for p in dashboard.get("projects") or [] if p.get("status") == "active"]
    suggestions: list[dict[str, Any]] = []

    suggestions.append(
        {
            "id": "telegram-export-intelligence",
            "title": "telegram-export-intelligence",
            "summary": "Навык для разбора экспортов Telegram Desktop в компактные карточки знаний, связи и рекомендации.",
            "why": "У вас уже есть исторический массив экспортов; без отдельного навыка они остаются статичным архивом.",
            "basedOn": [row["title"] for row in source_rows[:4]],
        }
    )

    if themes["inbox"] or "saved_messages" in source_titles:
        suggestions.append(
            {
                "id": "saved-messages-triage",
                "title": "saved-messages-triage",
                "summary": "Навык для превращения Saved Messages в решения: task, note, project, archive.",
                "why": "Личный inbox перегружен ссылками и заметками, но ценность появляется только после сортировки по типу действия.",
                "basedOn": [row["title"] for row in source_rows if row["theme"] in {"inbox", "planning"}][:4],
            }
        )

    if themes["ai-tools"] or themes["ai-business"]:
        suggestions.append(
            {
                "id": "channel-idea-distiller",
                "title": "channel-idea-distiller",
                "summary": "Навык для сжатия AI-каналов и подборок ботов в применимые паттерны и идеи для агентов.",
                "why": "Источники по ИИ и ботам дают много сигналов, но без стандарта быстро расползаются по заметкам.",
                "basedOn": [row["title"] for row in source_rows if row["theme"] in {"ai-tools", "ai-business"}][:4],
            }
        )

    if themes["family"] or themes["home"]:
        suggestions.append(
            {
                "id": "family-ops-briefing",
                "title": "family-ops-briefing",
                "summary": "Навык для семейных чатов: резюме, решения, события, покупки и контрольные списки.",
                "why": "Семейные источники лучше работают как операционная система дома, а не как набор разрозненных обсуждений.",
                "basedOn": [row["title"] for row in source_rows if row["theme"] in {"family", "home"}][:4],
            }
        )

    if themes["education"]:
        suggestions.append(
            {
                "id": "education-grant-radar",
                "title": "education-grant-radar",
                "summary": "Навык для систематизации школьных/грантовых идей и связывания их с текущими образовательными проектами.",
                "why": "В образовательных источниках уже есть материал для развития гимназических инициатив и грантовых заявок.",
                "basedOn": [row["title"] for row in source_rows if row["theme"] == "education"][:4],
            }
        )

    if active_project_titles:
        suggestions.append(
            {
                "id": "project-context-allocator",
                "title": "project-context-allocator",
                "summary": "Навык для автоматического распределения входящего по уже существующим проектам вместо создания дублей.",
                "why": "У вас много активных проектов, и новые идеи должны сразу падать в существующие контексты, если связь уже есть.",
                "basedOn": active_project_titles[:5],
            }
        )

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in suggestions:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique[:6]


def build_project_suggestions(source_rows: list[dict[str, Any]], topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active_topics = [t for t in topics if t.get("active")]
    topic_names = [t.get("name") for t in active_topics if t.get("name")]
    suggestions: list[dict[str, Any]] = []

    top_ai = [row["title"] for row in source_rows if row["theme"] in {"ai-tools", "ai-business"}][:4]
    top_family = [row["title"] for row in source_rows if row["theme"] in {"family", "home"}][:4]
    top_education = [row["title"] for row in source_rows if row["theme"] == "education"][:4]

    if top_ai:
        suggestions.append(
            {
                "title": "Telegram Knowledge Ops",
                "category": "работа",
                "summary": "Отдельный проект-оператор для переработки телеграм-источников в Obsidian, dashboard и backlog экспериментов.",
                "why": "Это снимет хаос между каналами, saved messages и вашими агентными проектами.",
                "basedOn": top_ai,
            }
        )
        suggestions.append(
            {
                "title": "AI Tools Atlas",
                "category": "работа",
                "summary": "Каталог практичных AI-ботов, каналов, workflows и сценариев применения для CLI/IDE-агентов.",
                "why": "В источниках уже накоплена база инструментов и AI-контента, которую можно превратить в ваш личный радар.",
                "basedOn": top_ai,
            }
        )

    if top_family:
        suggestions.append(
            {
                "title": "Family Operating System",
                "category": "семья",
                "summary": "Семейный слой знаний: события, подарки, дом, дети, решения, покупки и семейные проекты.",
                "why": "Семейные чаты содержат планирование и контекст, который полезнее держать как систему, а не как историю сообщений.",
                "basedOn": top_family,
            }
        )

    if top_education:
        suggestions.append(
            {
                "title": "Gymnasium Strategy Radar",
                "category": "работа",
                "summary": "Радар идей и возможностей для гимназии: развитие, гранты, контент, партнёры и инициативы.",
                "why": "Образовательные источники можно прямо связывать с уже существующими гимназическими проектами.",
                "basedOn": top_education,
            }
        )

    suggestions.append(
        {
            "title": "Interest-to-Project Router",
            "category": "я",
            "summary": "Маршрутизатор новых идей по вашим активным темам и ролям: я, семья, работа.",
            "why": "Сейчас источников становится больше, а значит нужна явная логика, куда должна попадать каждая новая мысль.",
            "basedOn": topic_names[:4],
        }
    )

    return suggestions[:6]


def build_processing_protocol() -> list[dict[str, str]]:
    return [
        {
            "step": "1. Захват",
            "detail": "Каждый новый источник получает карточку с путём, типом, датой, объёмом и признаком дубликата.",
        },
        {
            "step": "2. Сжатие",
            "detail": "Поток сразу переводится в короткое резюме: суть, сигналы, теги, возможное применение, а не в длинный пересказ.",
        },
        {
            "step": "3. Классификация",
            "detail": "Материал распределяется по двум осям: жизненная зона (я, семья, работа) и тема (AI, бизнес, образование, дом и т.д.).",
        },
        {
            "step": "4. Привязка",
            "detail": "Перед созданием новых сущностей проверяется связь с уже существующими проектами, workflows, навыками и областями интереса.",
        },
        {
            "step": "5. Решение",
            "detail": "Каждый элемент должен закончиться одним из статусов: задача, идея проекта, обновление skill, reference-note или архив.",
        },
        {
            "step": "6. Ревизия",
            "detail": "Раз в неделю смотрятся только топ-источники и новые дельты, а не весь архив целиком.",
        },
    ]


def build_feedback(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    areas = Counter(row["lifeArea"] for row in source_rows)
    themes = Counter(row["theme"] for row in source_rows)
    top_theme = themes.most_common(3)
    top_area = areas.most_common(3)
    overview = (
        "Текущий способ хранения уже дал сильный исторический архив, но без регулярного сжатия он начинает работать как склад, "
        "а не как система принятия решений. Лучший следующий уровень — считать Telegram не местом хранения, а только входной шиной."
    )
    recommendations = [
        "Держать отдельный слой triage для входящего, а не складывать сырые данные сразу в проекты.",
        "Считать Saved Messages и экспортированные каналы разными типами источников: личный inbox и тематические потоки.",
        "Каждую неделю пересматривать только топ-источники по рангу и новые дельты, чтобы не тонуть в историческом хвосте.",
        "Новые skills предлагать на основании повторяющихся паттернов, а не единичных интересных сообщений.",
    ]
    risks = [
        "В `telegram_inbox.py` лежат чувствительные токены и ключи в открытом виде; это стоит вынести в переменные окружения.",
        "Часть экспортов продублирована и есть повреждённые JSON; для истории это нормально, но для автоматизации нужен явный слой дедупликации.",
        "Без маршрутизации по жизненным зонам идеи из семьи, работы и личных интересов конкурируют в одной общей очереди.",
    ]
    return {
        "overview": overview,
        "topAreas": [{"area": AREA_LABELS.get(area, area), "count": count} for area, count in top_area],
        "topThemes": [{"theme": THEME_LABELS.get(theme, theme), "count": count} for theme, count in top_theme],
        "recommendations": recommendations,
        "risks": risks,
    }


def deduplicate_exports(digests: list[ExportDigest]) -> tuple[list[ExportDigest], dict[str, list[ExportDigest]]]:
    title_groups: dict[str, list[ExportDigest]] = defaultdict(list)
    for digest in digests:
        title_groups[normalize_title(digest.title)].append(digest)

    grouped: dict[str, list[ExportDigest]] = defaultdict(list)
    for digest in digests:
        title_key = normalize_title(digest.title)
        if title_key and len(title_groups[title_key]) > 1:
            digest.source_key = f"title:{slugify(digest.title)}"
            grouped[digest.source_key].append(digest)
        else:
            digest.source_key = digest.source_key
            grouped[digest.source_key].append(digest)

    chosen: list[ExportDigest] = []
    for items in grouped.values():
        items.sort(
            key=lambda item: (
                1 if item.valid else 0,
                item.message_count,
                item.last_date,
                str(item.primary_file),
            ),
            reverse=True,
        )
        chosen.append(items[0])
    chosen.sort(key=lambda item: (item.last_date, item.message_count, item.title), reverse=True)
    return chosen, grouped


def markdown_list(items: list[str]) -> str:
    if not items:
        return "- —"
    return "\n".join(f"- {item}" for item in items)


def relative_windows_path(path: Path) -> str:
    return str(path).replace("/", "\\")


def build_obsidian_notes(
    obsidian_root: Path,
    payload: dict[str, Any],
) -> None:
    source_dir = obsidian_root / SOURCE_NOTES_DIR
    source_dir.mkdir(parents=True, exist_ok=True)

    for source in payload["sources"]:
        file_name = f"{slugify(source['title'], 'source')}.md"
        note_path = source_dir / file_name
        body = f"""---
title: "{source['title'].replace('"', "'")}"
source_type: "{source['sourceType']}"
life_area: "{source['lifeArea']}"
theme: "{source['theme']}"
rank_score: {source['rankScore']}
message_count: {source['messageCount']}
last_date: "{source['lastDate']}"
tags: [{", ".join(f'"{tag}"' for tag in source['tags'])}]
---

# {source['title']}

## Суть
{source['summary']}

## Метаданные
- Жизненная зона: {AREA_LABELS.get(source['lifeArea'], source['lifeArea'])}
- Тема: {THEME_LABELS.get(source['theme'], source['theme'])}
- Ранг: {source['rankScore']}
- Сообщений: {source['messageCount']}
- Период: {date_label(source['firstDate'])} — {date_label(source['lastDate'])}
- Формат: {", ".join(source['formats'])}
- Основной путь: `{source['primaryPath']}`

## Связи
{markdown_list([f"[[Projects/AI Workspace/{item['id']}]] — {item['title']}" for item in source['relatedProjects']])}

## Принципы применения
{markdown_list(source['applicationPrinciples'])}

## Сигналы
- Ключевые слова: {", ".join(source['topKeywords']) or "—"}
- Домены: {", ".join(source['topDomains']) or "—"}
- Упоминания: {", ".join(source['topMentions']) or "—"}

## Короткие фрагменты
{markdown_list(source['sampleMessages'])}

## Файлы экспорта
{markdown_list([f"`{path}`" for path in source['allPaths']])}
"""
        note_path.write_text(body, encoding="utf-8")

    summary = payload["summary"]
    summary_note = obsidian_root / SOURCE_SUMMARY_NOTE
    summary_note.parent.mkdir(parents=True, exist_ok=True)
    summary_note.write_text(
        f"""# Telegram Desktop Intelligence

- Обновлено: **{payload['meta']['generatedAt']}**
- Экспортов: **{payload['stats']['exportsScanned']}**
- Уникальных источников: **{payload['stats']['uniqueSources']}**
- Дубликатов: **{payload['stats']['duplicateExports']}**
- Сообщений в лучших копиях: **{payload['stats']['messageCount']}**

## Обзор
{summary['overview']}

## Лучшие источники
{markdown_list([f"[[Inbox/Telegram Desktop Intelligence/Sources/{slugify(item['title'], 'source')}]] — {item['rankScore']}/100" for item in payload['sources'][:10]])}

## Предложения по навыкам
{markdown_list([f"**{item['title']}** — {item['summary']}" for item in payload['skillSuggestions']])}

## Предложения по проектам
{markdown_list([f"**{item['title']}** — {item['summary']}" for item in payload['projectSuggestions']])}

## Протокол обработки входящего
{markdown_list([f"**{item['step']}** — {item['detail']}" for item in payload['processingProtocol']])}
""",
        encoding="utf-8",
    )

    overview_note = obsidian_root / SOURCE_OVERVIEW_NOTE
    overview_note.parent.mkdir(parents=True, exist_ok=True)
    overview_note.write_text(
        f"""# Telegram Desktop Intelligence

- Обновлено: **{payload['meta']['generatedAt']}**
- Уникальных источников: **{payload['stats']['uniqueSources']}**
- Топ-темы: **{", ".join(item['theme'] for item in summary['topThemes'])}**

## Краткая оценка процесса
{summary['overview']}

## Что улучшить
{markdown_list(summary['recommendations'])}

## Риски
{markdown_list(summary['risks'])}

## Карта зон
{markdown_list([f"**{bucket['label']}** — {bucket['count']} источников" for bucket in payload['areaBuckets']])}
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Telegram Desktop intelligence for dashboard and Obsidian.")
    parser.add_argument("--exports-root", default=str(DEFAULT_EXPORTS_ROOT))
    parser.add_argument("--dashboard-data", default=str(DEFAULT_DASHBOARD_DATA))
    parser.add_argument("--topics-json", default=str(DEFAULT_TOPICS_JSON))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    parser.add_argument("--out-markdown")
    parser.add_argument("--obsidian-root")
    args = parser.parse_args()

    workspace_root = Path.cwd()
    exports_root = Path(args.exports_root)
    dashboard_data_path = Path(args.dashboard_data)
    if not dashboard_data_path.is_absolute():
        dashboard_data_path = workspace_root / dashboard_data_path
    topics_path = Path(args.topics_json)
    out_json_path = Path(args.out_json)
    if not out_json_path.is_absolute():
        out_json_path = workspace_root / out_json_path
    out_markdown_path = Path(args.out_markdown) if args.out_markdown else workspace_root / "docs" / f"telegram_desktop_analysis_{date.today().isoformat()}.md"

    digests: list[ExportDigest] = []
    for export_dir in sorted(exports_root.glob("ChatExport*")):
        if not export_dir.is_dir():
            continue
        result_json = export_dir / "result.json"
        messages_html = export_dir / "messages.html"
        if result_json.exists():
            digests.append(parse_result_json(result_json))
        elif messages_html.exists():
            digests.append(parse_html_export(messages_html))

    chosen, grouped = deduplicate_exports(digests)
    dashboard = load_dashboard_context(dashboard_data_path)
    topics = load_topics(topics_path)
    topic_tokens = {
        topic.get("name", ""): set(tokenise(f"{topic.get('name', '')} {topic.get('description', '')}"))
        for topic in topics
        if topic.get("active")
    }
    projects = dashboard.get("projects") or []
    projects_enriched = []
    for project in projects:
        projects_enriched.append(
            {
                "id": project.get("id"),
                "title": project.get("title"),
                "status": project.get("status"),
                "tokens": project_tokens(project),
            }
        )

    today_value = date.today()
    source_rows: list[dict[str, Any]] = []
    area_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total_messages = 0
    duplicate_count = 0

    for digest in chosen:
        duplicates = grouped[digest.source_key]
        duplicate_count += max(0, len(duplicates) - 1)
        total_messages += digest.message_count

        top_keywords = format_top_entries(digest.token_counter, limit=7)
        theme = theme_from_digest(digest.title, top_keywords + format_top_entries(digest.hashtags, 5))
        life_area = area_from_title_theme(digest.title, theme)
        token_set = set(top_keywords) | set(tokenise(digest.title))

        related_projects = []
        for project in projects_enriched:
            overlap = token_set & project["tokens"]
            if len(overlap) >= 1:
                related_projects.append(
                    {
                        "id": project["id"],
                        "title": project["title"],
                        "status": project["status"],
                        "overlap": sorted(overlap),
                    }
                )
        related_projects.sort(key=lambda item: (len(item["overlap"]), item["status"] == "active"), reverse=True)
        related_projects = related_projects[:4]

        topic_matches = []
        for topic_name, tokens in topic_tokens.items():
            overlap = token_set & tokens
            if overlap:
                topic_matches.append({"name": topic_name, "overlap": sorted(overlap)})
        topic_matches.sort(key=lambda item: len(item["overlap"]), reverse=True)

        rank_score = compute_rank_score(
            digest=digest,
            theme=theme,
            related_projects_count=len(related_projects),
            topic_matches_count=len(topic_matches),
            today_value=today_value,
        )
        summary = summarize_source(digest.title, theme, digest, related_projects)
        principles = determine_application_principles(digest.title, theme, digest, related_projects)
        domains = extract_domains(digest.links)
        senders = [item for item, _ in digest.sender_counter.most_common(4)]

        row = {
            "id": slugify(f"{digest.source_id}-{digest.title}", "source"),
            "sourceId": digest.source_id,
            "title": digest.title,
            "lifeArea": life_area,
            "lifeAreaLabel": AREA_LABELS.get(life_area, life_area),
            "theme": theme,
            "themeLabel": THEME_LABELS.get(theme, theme),
            "rankScore": rank_score,
            "messageCount": digest.message_count,
            "firstDate": digest.first_date,
            "lastDate": digest.last_date,
            "formats": sorted({item.export_format for item in duplicates}),
            "sourceType": digest.source_type,
            "valid": digest.valid,
            "parseStatus": digest.parse_status,
            "summary": summary,
            "applicationPrinciples": principles,
            "topKeywords": top_keywords,
            "topDomains": domains,
            "topMentions": format_top_entries(digest.mentions, limit=5),
            "topHashtags": format_top_entries(digest.hashtags, limit=5),
            "topSenders": senders,
            "sampleMessages": digest.sample_messages[:5],
            "mediaCount": digest.media_count,
            "fileCount": digest.file_count,
            "duplicateCount": max(0, len(duplicates) - 1),
            "primaryPath": relative_windows_path(digest.export_dir),
            "allPaths": [relative_windows_path(item.export_dir) for item in duplicates],
            "primaryFile": relative_windows_path(digest.primary_file),
            "relatedProjects": related_projects,
            "relatedTopics": topic_matches[:4],
            "tags": [
                "telegram",
                f"area/{slugify(life_area, 'area')}",
                f"theme/{slugify(theme, 'theme')}",
                *(f"project/{slugify(item['id'], 'project')}" for item in related_projects[:3]),
            ],
        }
        source_rows.append(row)
        area_buckets[life_area].append(row)

    source_rows.sort(key=lambda item: (item["rankScore"], item["messageCount"], item["title"]), reverse=True)
    area_bucket_rows = []
    for area in ("работа", "я", "семья"):
        rows = area_buckets.get(area, [])
        if not rows:
            continue
        theme_counter = Counter(item["theme"] for item in rows)
        area_bucket_rows.append(
            {
                "id": slugify(area, "area"),
                "area": area,
                "label": AREA_LABELS.get(area, area),
                "count": len(rows),
                "topThemes": [THEME_LABELS.get(theme, theme) for theme, _ in theme_counter.most_common(3)],
                "sourceTitles": [item["title"] for item in rows[:6]],
            }
        )

    skill_suggestions = build_skill_suggestions(source_rows, dashboard)
    project_suggestions = build_project_suggestions(source_rows, topics)
    processing_protocol = build_processing_protocol()
    feedback = build_feedback(source_rows)

    payload = {
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "exportsRoot": relative_windows_path(exports_root),
            "dashboardData": relative_windows_path(dashboard_data_path),
            "topicsSource": relative_windows_path(topics_path),
            "manualJsonTool": r"C:\Program Files\Google\Chrome\Application\chrome_proxy.exe",
        },
        "stats": {
            "exportsScanned": len(digests),
            "uniqueSources": len(source_rows),
            "duplicateExports": duplicate_count,
            "messageCount": total_messages,
            "jsonSources": sum(1 for row in source_rows if "json" in row["formats"]),
            "htmlSources": sum(1 for row in source_rows if "html" in row["formats"]),
            "invalidJsonFallbacks": sum(1 for row in source_rows if row["parseStatus"] != "ok"),
        },
        "summary": feedback,
        "sources": source_rows,
        "areaBuckets": area_bucket_rows,
        "skillSuggestions": skill_suggestions,
        "projectSuggestions": project_suggestions,
        "processingProtocol": processing_protocol,
    }

    write_json(out_json_path, payload)

    out_markdown_path.parent.mkdir(parents=True, exist_ok=True)
    out_markdown_path.write_text(
        f"""# Telegram Desktop Analysis

- Обновлено: **{payload['meta']['generatedAt']}**
- Экспортов: **{payload['stats']['exportsScanned']}**
- Уникальных источников: **{payload['stats']['uniqueSources']}**
- Дубликатов: **{payload['stats']['duplicateExports']}**
- Сообщений в выбранных копиях: **{payload['stats']['messageCount']}**

## Резюме
{payload['summary']['overview']}

## Распределение по зонам
{markdown_list([f"**{item['label']}** — {item['count']} источников; темы: {', '.join(item['topThemes'])}" for item in payload['areaBuckets']])}

## Топ-источники
{markdown_list([f"**{item['title']}** — {item['rankScore']}/100; {item['summary']}" for item in payload['sources'][:10]])}

## Предложения по навыкам
{markdown_list([f"**{item['title']}** — {item['summary']}" for item in payload['skillSuggestions']])}

## Предложения по проектам
{markdown_list([f"**{item['title']}** — {item['summary']}" for item in payload['projectSuggestions']])}

## Протокол обработки входящего
{markdown_list([f"**{item['step']}** — {item['detail']}" for item in payload['processingProtocol']])}

## Рекомендации
{markdown_list(payload['summary']['recommendations'])}

## Риски
{markdown_list(payload['summary']['risks'])}
""",
        encoding="utf-8",
    )

    if args.obsidian_root:
        build_obsidian_notes(Path(args.obsidian_root), payload)


if __name__ == "__main__":
    main()
    raise SystemExit(0)

    overview_note = obsidian_root / SOURCE_OVERVIEW_NOTE
    overview_note.parent.mkdir(parents=True, exist_ok=True)
    overview_note.write_text(
        f"""# Telegram Desktop Intelligence

- Обновлено: **{payload['meta']['generatedAt']}**
- Уникальных источников: **{payload['stats']['uniqueSources']}**
- Топ-темы: **{", ".join(item['theme'] for item in summary['topThemes'])}**

## Краткая оценка процесса
{summary['overview']}

## Что улучшить
{markdown_list(summary['recommendations'])}

## Риски
{markdown_list(summary['risks'])}

## Карта зон
{markdown_list([f"**{bucket['label']}** — {bucket['count']} источников" for bucket in payload['areaBuckets']])}
""",
        encoding="utf-8",
    )
