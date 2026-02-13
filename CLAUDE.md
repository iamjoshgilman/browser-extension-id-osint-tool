# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Browser Extension OSINT Tool — a web application for investigating browser extensions across Chrome Web Store, Firefox Add-ons, and Microsoft Edge Add-ons. It provides a unified search interface for security researchers and IT administrators to look up extension metadata across stores.

## Commands

```bash
# Install dependencies
make install                  # pip install -r backend/requirements.txt

# Run development server (Flask on port 5000)
make dev                      # FLASK_ENV=development, runs backend/app.py

# Run production server
make prod                     # gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# Run all tests
make test                     # cd backend && python -m pytest ../tests -v

# Run a single test file
cd backend && python -m pytest ../tests/test_api.py -v

# Run tests matching a pattern
cd backend && python -m pytest ../tests -k "test_health" -v

# Lint
make lint                     # flake8 --max-line-length=100

# Format
make format                   # black --line-length=100

# Docker
make docker-build && make docker-up
```

## Architecture

**Backend** (Python 3.11 / Flask 3.0): `backend/`
- `app.py` — Flask application with route handlers (`/api/search`, `/api/bulk-search`, `/api/stats`, `/api/health`, `/api/cleanup`)
- `config.py` — Config classes selected by `FLASK_ENV` env var (development/production/testing)
- `middleware.py` — Decorators: `@require_api_key`, `@validate_json`, `@sanitize_input`, `@log_request`
- `database/manager.py` — SQLite cache layer with 7-day TTL; tables: `extension_cache` (UNIQUE on extension_id+store), `search_history`
- `models/extension.py` — `ExtensionData` dataclass with `to_dict()`/`from_dict()` serialization

**Scrapers** (`backend/scrapers/`): All inherit from `ExtensionScraper` (ABC in `base.py`) which defines `scrape()`, `validate_id()`, `normalize_id()`, `get_extension_url()`.
- `chrome.py` — Fetches HTML from Chrome Web Store, extracts JSON-LD structured data with BeautifulSoup fallback
- `firefox.py` — Uses official Firefox Add-ons API v5 (JSON), handles localized fields
- `edge.py` — Uses Microsoft Edge API (`getproductdetailsbycrxid`); **known issue: currently returns "unknown" for some fields**

**Frontend** (`frontend/`): Vanilla JS/HTML/CSS, no build step. Catppuccin Frapp theme. `js/api.js` wraps API calls, `js/app.js` handles UI logic.

**Infrastructure**: Nginx reverse proxy (`nginx/`), Docker Compose (`docker/`) with backend + frontend + optional Redis for rate limiting.

## Request Flow

1. Frontend POSTs to `/api/search` with `{extension_id, stores[]}`
2. Rate limit check (30/min search, 10/min bulk) → optional API key validation
3. For each store: check SQLite cache → on miss, dispatch to store-specific scraper → cache result
4. Return JSON with extension metadata per store

## Key Conventions

- Line length: 100 chars (both flake8 and black)
- Tests use pytest fixtures: `test_client` (Flask test client), `temp_db` (temp SQLite)
- Tests run from `backend/` directory with test files in `../tests/`
- Extension ID formats: Chrome = 32 lowercase letters, Firefox = flexible (UUID/email/string), Edge = 32 alphanumeric
- Config reads from environment variables with sensible defaults; see `.env.example`
