# AGENTS.md — News Push App

FastAPI + WeChat + DashScope(LLM) + APScheduler notification push service.

## Quick Start

```bash
cp .env.example .env   # then fill in real keys
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

```
user message → app/api/wechat.py → app/services/interaction.py
                                      ├── llm.py (DashScope intent + chat)
                                      ├── weather.py → adapters/moji_weather_mcp.py
                                      ├── news.py     → adapters/city_news_mcp.py
                                      └── location.py → adapters/gaode_map_mcp.py
```

**Entry points:**
- `app/main.py` — FastAPI app creation, lifecycle hooks, routes
- `app/api/wechat.py` — `GET /api/wechat` (WeChat verification), `POST /api/wechat` (message handling)
- `config/config.py` — all configuration loaded from `.env` via `python-dotenv`

## Critical Gotchas

### Adapters are ALL stubs — no real API calls
All three adapters (`moji_weather_mcp.py`, `city_news_mcp.py`, `gaode_map_mcp.py`) return **hardcoded mock data**. The `self.base_url = "mcp://..."` is decorative — no MCP protocol or HTTP calls are actually made. To connect real APIs, replace the adapter implementations entirely.

### Indentation bug in interaction.py
`app/services/interaction.py` has an indentation error: `generate_weather_response`, `generate_news_response`, etc. (lines 33–156) are nested inside `__init__` rather than being class methods. The code happens to work because Python allows this, but do NOT follow this pattern when adding methods.

### In-memory user storage — no persistence
User data is stored in a global dict (`user_db` in `app/models/user.py`). All data is lost on restart. This is intentional for the template — replace with a database for production.

### Singleton pattern — import the instance, don't instantiate
Every service uses `__new__` singleton. Always use the module-level instance:
```python
from app.services.weather import weather_service    # ✅ correct
ws = WeatherService()                                  # ❌ may create issues
```

### WeChat verification fails without real public URL
The `GET /api/wechat` endpoint requires WeChat's signature verification. During local dev, this **will fail** unless you use ngrok and configure the real WeChat backend. The scheduler and push logic are unaffected by this.

### Config validation differs by DEBUG mode
- `DEBUG=true`: only DASHSCOPE_API_KEY is required
- `DEBUG=false`: WECHAT_TOKEN, WECHAT_APPID, WECHAT_APPSECRET also required

### The term "MCP" is ambiguous in this repo
The README describes MCP as "Model-View-Controller-Presenter", but the adapter directory and class names reference "MCP services" (Model Context Protocol). Neither is actually implemented — they're stub/mock services.

## Running Tests

```bash
# default test runner
python -m unittest discover tests

# pytest also works
pytest tests/ -v
```

Tests call the adapter stubs directly — no mocking required. Tests hit real DashScope API for LLM service tests (line 162–172 of `test_services.py`) unless mocked via `@patch`.

## Scheduled Tasks

Configured in `app/services/scheduler.py`:
- **Daily push**: `PUSH_TIME_HOUR`:`PUSH_TIME_MINUTE` (default 08:00) — sends weather+news to all in-memory users via WeChat
- **News cache refresh**: every 2 hours
- **Weather cache refresh**: every 1 hour
- **Health check**: every 30 minutes
- **Cache cleanup**: daily at 02:00
- **Weekly report**: Monday 09:00

Timezone: `SCHEDULER_TIMEZONE` (default `Asia/Shanghai`). Requires `pytz` (optional — falls back to no timezone if missing).

## Docker

```bash
docker build -t news-push-app .
docker run -d --name news-push-app -p 8000:8000 --env-file .env news-push-app
```

- Base image: `python:3.9-slim`
- Runs as non-root user `appuser` (UID 1001)
- Health check: `curl http://localhost:8000/health`
- `.dockerignore` excludes tests, docs, git files, and IDE configs

## Key environment variables

| Variable | Default | Required |
|---|---|---|
| `DASHSCOPE_API_KEY` | — | Yes |
| `WECHAT_TOKEN` | — | Prod only |
| `WECHAT_APPID` | — | Prod only |
| `WECHAT_APPSECRET` | — | Prod only |
| `DEFAULT_CITY` | 北京 | No |
| `PUSH_TIME_HOUR` | 8 | No |
| `PUSH_TIME_MINUTE` | 0 | No |
| `DASHSCOPE_MODEL` | qwen-turbo | No |
| `LOG_LEVEL` | INFO | No |

## Project conventions

- **No formatter/linter config exists** — do not enforce formatting consistency beyond what's already there
- **No CI/CD** — no GitHub Actions, no pre-commit hooks
- **No database** — everything is in-memory
- **No type checker config** — `mypy`/`pyright` not configured
- **`app/utils/` is intentionally empty** — placeholder for future shared utilities
- **`app/__init__.py` is empty** — don't add imports here without reason
