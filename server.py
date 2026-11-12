#!/usr/bin/env python3
"""
Offline study-chatbot backend — standard library only, no internet.

Frontend (web/index.html) is ONLY for:
  - typing a question
  - adding / updating a note (title + content + which file)
Backend (this file) does ALL the work:
  - loads notes/ , scores and searches them (from chatbot.py)
  - saves a new note section to the chosen .md file, then reloads
  - refuses with "Not in your notes" when nothing matches

Run:
    python server.py
Then open in your browser (no internet needed, it's your own computer):
    http://localhost:8000

API (all local):
    GET  /api/notes          -> {"files": [...], "notes": [{file, title}]}
    POST /api/ask            -> {"question": ...}
                                {"found": true, "source": ..., "title": ...,
                                 "text": ..., "score": ...}
                                or {"found": false, "text": "Not in your notes."}
    POST /api/notes          -> {"file": "dbms.md", "title": "...",
                                 "content": "..."}
                                Appends "# <title>\n\n<content>" to notes/<file>
                                and reloads the search index immediately,
                                so the new note is searchable at once.
    GET  /api/note?file=X&title=Y -> {"file": ..., "title": ...,
                                      "text": ...} for one note section
    PUT  /api/notes          -> {"file": ..., "old_title": ...,
                                 "title": "...", "content": "..."}
                                Replaces that section in the file, reloads.
    DELETE /api/notes        -> {"file": ..., "title": ...}
                                Removes that section from the file, reloads.
"""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import chatbot

BASE = Path(__file__).parent
NOTES_DIR = BASE / "notes"
WEB_DIR = BASE / "web"
PORT = 8000

# Search index, rebuilt whenever notes change.
CHUNKS = []
IDF = {}
_LAST_SNAPSHOT = None


def _snapshot():
    """(filename, size, mtime) for every note file — cheap change detector."""
    snap = []
    for path in sorted(NOTES_DIR.glob("*.md")) + sorted(NOTES_DIR.glob("*.txt")):
        try:
            stat = path.stat()
            snap.append((path.name, stat.st_size, stat.st_mtime_ns))
        except OSError:
            continue
    return snap


def reload_index():
    global CHUNKS, IDF, _LAST_SNAPSHOT
    CHUNKS = chatbot.load_notes(NOTES_DIR)
    IDF = chatbot.build_idf(CHUNKS)
    _LAST_SNAPSHOT = _snapshot()


def maybe_reload():
    """If files were dropped in / edited / deleted in notes/ while the
    server is running, rebuild the index before answering — so no
    restart is needed to pick up your own files."""
    global _LAST_SNAPSHOT
    if _LAST_SNAPSHOT is None or _snapshot() != _LAST_SNAPSHOT:
        reload_index()


reload_index()


def parse_sections(text):
    """Split a note file into (level, title, body) sections, one per heading.
    Mirrors chatbot.load_notes: any '#', '##' or '###' heading starts a section."""
    headings = list(re.finditer(r"(?m)^(#{1,3})\s+(.+)$", text))
    sections = []
    for i, match in enumerate(headings):
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        sections.append({
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
            "body": text[start:end].strip(),
        })
    return sections


def render_sections(sections):
    return "\n\n".join(
        f"{'#' * s['level']} {s['title']}\n\n{s['body']}"
        for s in sections if s["body"] or True
    ) + ("\n" if sections else "")


def safe_filename(name):
    """Only allow a plain .md filename inside notes/ — no paths, no tricks."""
    name = (name or "").strip()
    if not name.endswith(".md"):
        name += ".md"
    name = re.sub(r"[^A-Za-z0-9_.\-]", "_", name)
    if name in (".md", "..md") or ".." in name:
        return "notes.md"
    return name


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the terminal clean

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/api/notes", "/api/note"):
            maybe_reload()
        if path == "/api/notes":
            files = sorted(p.name for p in NOTES_DIR.glob("*.md"))
            notes = [{"file": c["source"], "title": c["title"]} for c in CHUNKS]
            self._send_json({"files": files, "notes": notes})
            return
        if path == "/api/note":
            query = parse_qs(parsed.query)
            filename = safe_filename(query.get("file", [""])[0])
            title = query.get("title", [""])[0]
            for chunk in CHUNKS:
                if chunk["source"] == filename and chunk["title"] == title:
                    self._send_json({"file": filename, "title": title,
                                     "text": chunk["text"].strip()})
                    return
            self._send_json({"error": "Note not found."}, 404)
            return
        # Everything else is a static file from web/ (default: index.html)
        target = WEB_DIR / "index.html" if path in ("/", "/index.html") else WEB_DIR / path.lstrip("/")
        if not target.is_file() or WEB_DIR not in target.resolve().parents:
            self.send_response(404)
            self.end_headers()
            return
        body = target.read_bytes()
        ctype = "text/html" if target.suffix == ".html" else "text/plain"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path == "/api/reload":
            reload_index()
            self._send_json({"reloaded": True,
                             "sections": len(CHUNKS),
                             "files": len({c["source"] for c in CHUNKS})})
            return
        if path == "/api/ask":
            maybe_reload()
            question = (data.get("question") or "").strip()
            chunk, score = chatbot.answer(question, CHUNKS, IDF)
            if chunk is None:
                self._send_json({"found": False, "text": "Not in your notes."})
            else:
                self._send_json({
                    "found": True,
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "text": chunk["text"].strip(),
                    "score": round(score, 1),
                })
            return
        if path == "/api/notes":
            title = (data.get("title") or "").strip()
            content = (data.get("content") or "").strip()
            if not title or not content:
                self._send_json({"error": "Title and content are both required."}, 400)
                return
            filename = safe_filename(data.get("file") or "notes.md")
            filepath = NOTES_DIR / filename
            section = f"\n\n# {title}\n\n{content}\n"
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(section)
            reload_index()
            self._send_json({"saved": True, "file": filename, "title": title})
            return
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path != "/api/notes":
            self.send_response(404)
            self.end_headers()
            return
        filename = safe_filename(data.get("file") or "")
        old_title = (data.get("old_title") or "").strip()
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()
        if not old_title or not title or not content:
            self._send_json({"error": "Old title, new title and content are required."}, 400)
            return
        filepath = NOTES_DIR / filename
        if not filepath.is_file():
            self._send_json({"error": "File not found."}, 404)
            return
        sections = parse_sections(filepath.read_text(encoding="utf-8"))
        for section in sections:
            if section["title"] == old_title:
                section["title"] = title
                section["body"] = content
                break
        else:
            self._send_json({"error": "Note not found in that file."}, 404)
            return
        filepath.write_text(render_sections(sections), encoding="utf-8")
        reload_index()
        self._send_json({"saved": True, "file": filename, "title": title})

    def do_DELETE(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path != "/api/notes":
            self.send_response(404)
            self.end_headers()
            return
        filename = safe_filename(data.get("file") or "")
        title = (data.get("title") or "").strip()
        filepath = NOTES_DIR / filename
        if not filepath.is_file():
            self._send_json({"error": "File not found."}, 404)
            return
        sections = parse_sections(filepath.read_text(encoding="utf-8"))
        kept = [s for s in sections if s["title"] != title]
        if len(kept) == len(sections):
            self._send_json({"error": "Note not found in that file."}, 404)
            return
        filepath.write_text(render_sections(kept), encoding="utf-8")
        reload_index()
        self._send_json({"deleted": True, "file": filename, "title": title})


if __name__ == "__main__":
    print(f"Study chatbot running offline at http://localhost:{PORT}")
    print("Open that address in your browser. Press Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
