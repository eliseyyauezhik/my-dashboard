#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
IDEA_INBOX_PATH = WORKSPACE_ROOT / "data" / "idea_inbox.json"


def slugify(value: str, fallback: str = "item") -> str:
    text = value.strip().lower()
    chars: list[str] = []
    for char in text:
        if char.isalnum() or char in {"-", "_"}:
            chars.append(char)
        elif char.isspace():
            chars.append("-")
    slug = "".join(chars).strip("-_")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or fallback


def load_inbox() -> dict:
    if not IDEA_INBOX_PATH.exists():
        return {"ideas": []}
    with IDEA_INBOX_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        return {"ideas": []}
    payload.setdefault("ideas", [])
    return payload


def save_inbox(payload: dict) -> None:
    IDEA_INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with IDEA_INBOX_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE_ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/idea-inbox":
            self._send_json(load_inbox())
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/idea-inbox/ideas":
            self._send_json({"error": "Unknown endpoint"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return

        title = str(payload.get("title", "")).strip()
        if not title:
            self._send_json({"error": "Field 'title' is required"}, status=HTTPStatus.BAD_REQUEST)
            return

        inbox = load_inbox()
        tags = payload.get("tags", [])
        if isinstance(tags, str):
            tags = [item.strip() for item in tags.split(",") if item.strip()]
        if not isinstance(tags, list):
            tags = []

        item = {
            "id": f"draft-{slugify(title, 'idea')}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "description": str(payload.get("description", "")).strip(),
            "comment": str(payload.get("comment", "")).strip(),
            "group": str(payload.get("group", "")).strip(),
            "relatedProject": str(payload.get("relatedProject", "")).strip(),
            "priority": str(payload.get("priority", "medium")).strip() or "medium",
            "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
            "addedDate": datetime.now().date().isoformat(),
            "source": "mindmap_dashboard",
        }
        inbox["ideas"].append(item)
        save_inbox(inbox)
        self._send_json({"ok": True, "idea": item}, status=HTTPStatus.CREATED)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve dashboard files with idea inbox API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8891)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"DASHBOARD_SERVER: http://{args.host}:{args.port}/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
