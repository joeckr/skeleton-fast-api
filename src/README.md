# Backend Package (`src`)

This directory contains the FastAPI application codebase, dependencies, and test suite.

---

## Package Architecture

```text
src/
├── api/             # Outbound integrations (e.g. OIDC discovery & JWKS fetching)
├── auth/            # Authentication providers (none, basic, oidc)
├── controllers/     # Business logic handlers decoupled from routing
├── cron/            # Asynchronous background tasks managed by lifespan
├── endpoints/       # Route definitions (APIRouter) grouped by domain
├── logger/          # Structured console logging functions
├── startup/         # Framework initialization (auth, cors, cron, errors, logging)
├── tests/           # Automated pytest suite
└── main.py          # Application entrypoint & create_app factory
```

---

## Developing in `src`

### Virtual Environment & Dependencies

Dependencies are pinned in `pyproject.toml` and managed by `uv`:

```bash
# Install production and development dependencies
uv sync

# Add a runtime dependency
uv add <package>

# Add a development/test dependency
uv add --dev <package>
```

### Running the App

```bash
# Start with auto-reloading
uv run fastapi dev main.py --port 8000

# Start with production runner
uv run fastapi run main.py --port 8000
```

### Running Tests

```bash
uv run pytest -v
```

---

## Adding New Features

### 1. Adding a New Endpoint
1. Create a business logic function in `src/controllers/<domain>.py`.
2. Create an `APIRouter` in `src/endpoints/<domain>.py` and bind the controller.
3. Register the router in `src/startup/endpoints.py` via `app.include_router(...)`.
4. Add test cases in `src/tests/test_<domain>.py`.

### 2. Adding a Scheduled Job
1. Implement your async task in `src/cron/<job_name>.py`.
2. Register the task inside `start_cron_tasks` in `src/cron/__init__.py`.
3. Add any interval settings to `src/startup/env.py`.
