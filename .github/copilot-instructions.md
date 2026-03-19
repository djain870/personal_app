## Quick orientation — what this project is

This is a small FastAPI-based personal app that combines three core features: finance tracking, document uploads, and a chat assistant. It uses server-side Jinja2 templates and a local SQLite database (`finance.db`). Static/uploads are served from `data/` and templates live in `templates/`.

## High-level architecture

- FastAPI application entry: `main.py` — defines HTTP routes, mounts static files (`/data`) and calls `Base.metadata.create_all(...)` at import time.
- ORM layer: `models.py` — SQLAlchemy declarative models: `Expense`, `Document`, `Chat`, `User`.
- DB wiring: `database.py` — `engine`, `SessionLocal`, `Base`. Uses SQLite via `sqlite:///./finance.db` (no migrations).
- Templates: `templates/*.html` — server-rendered pages (e.g. `finances.html`, `documents.html`, `chat.html`).
- Uploads: `data/documents/` — saved files; `Document.file_path` stores absolute/relative path.

Data flow notes:
- Routes create a new SQLAlchemy `SessionLocal()` and explicitly close it. Look for `db = SessionLocal()` / `db.close()` in `main.py`.
- Authentication is cookie-based and minimal: username stored in a cookie (`request.cookies.get('user')`). Passwords are plaintext in the DB (see `User` model) — important when making changes.

Key integration points and external deps

- News API: `main.py` calls `requests.get()` against `newsapi.org` (API key hardcoded currently). See `/news` route.
- Chat / LLM: `main.py` uses `openai.OpenAI()` with a custom `base_url` (HuggingFace router) and a hardcoded HF key; model used is `meta-llama/Meta-Llama-3-8B-Instruct`. See `/chat` route for the full prompt construction.
- Serve static/uploaded files via FastAPI: `app.mount('/data', StaticFiles(directory='data'), name='data')` — uploaded documents are available under `/data/documents/<filename>`.

Developer workflows (how to run & debug)

1. Create a virtual environment and install dependencies (minimum):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn sqlalchemy jinja2 requests openai
```

2. Start the dev server (reloads on changes):

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

3. Smoke checks:
- Open `http://127.0.0.1:8000/` for index.
- `http://127.0.0.1:8000/finances` — needs a cookie-based user; use `/create-user` or `/signup` to add a user and `/login` to set cookie.
- `http://127.0.0.1:8000/documents` — upload saves to `data/documents/` and DB `documents` table.

Project-specific conventions & patterns (useful for an AI agent)

- Synchronous handlers only: all route functions are plain sync functions (no `async`). When editing, preserve sync behavior or convert carefully.
- DB lifecycle: each route creates/closes sessions manually; prefer following this pattern when adding routes (do not assume a global session).
- Templates are server-side Jinja2; routes return `templates.TemplateResponse("name.html", {"request": request, ...})`.
- Routes use cookie key `user` for the current username — search for `request.cookies.get("user")`.
- File storage pattern: uploaded file → written to `data/documents/<filename>` → DB row created with `file_path` (remove file on delete route).

Files to look at when making changes

- `main.py` — all route logic (finance CRUD, documents, news, chat, auth). Primary change surface.
- `models.py` — database schema. Add fields here and rely on `Base.metadata.create_all(...)` to create tables in development.
- `database.py` — DB connection config and session maker.
- `templates/` — UI; names match routes (`finances.html`, `finances_edit.html`, `documents.html`, `chat.html`, etc.).

Security & operational caveats (discoverable, not opinionated)

- Secrets are in-source: API keys for News API and OpenAI/HF are hardcoded in `main.py`. Running the chat/news endpoints may fail or leak keys if not handled. If altering those routes, keep the current literal usage in mind.
- No migrations: schema changes are applied via `Base.metadata.create_all(...)` only — this is fine for dev but there is no Alembic or migration history.

Examples (copy/paste patterns)

- Querying expenses filtered by month and user (from `main.py`):

```py
db = SessionLocal()
expenses = db.query(Expense).filter(Expense.date.startswith(month), Expense.user == user).all()
db.close()
```

- Saving an upload (from `main.py`): write file, create `Document` row, commit, redirect to `/documents`.

If you need changes to how secrets, sessions, or uploads work, ask what trade-offs you want (quick local fix vs. production-safe refactor). I can update the file with environment variable pulls, add a `.env` loader, or introduce a lightweight migration path.

Please review and tell me if you'd like me to:
- replace hardcoded API keys with env var lookups, or
- add a `requirements.txt` and a short `README.md` with run instructions.

— End of file
