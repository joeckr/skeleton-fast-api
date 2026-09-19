# skeleton-fast-api

A modular, production-ready FastAPI skeleton designed for containerized deployments on Kubernetes. Features pluggable authentication, centralized structured logging, background cron jobs, standardized error envelopes, controller architecture, and an automated test suite.

---

## Features

- **Controller & Router Separation**: Clean architecture separating route definitions (`endpoints/`) from business logic (`controllers/`).
- **Pluggable Authentication**: Middleware supporting multiple auth strategies configured via `AUTH_MODE`:
  - `none`: Permissive / anonymous development mode.
  - `basic`: HTTP Basic authentication for containers and test harnesses.
  - `oidc`: OpenID Connect JWT validation with automatic JWKS key discovery and caching.
- **Strict Probe Exclusion**: Only Kubernetes health probes (`/health/live` and `/health/ready`) bypass authentication.
- **Centralized Structured Logging**: Request-scoped correlation IDs (`X-Request-ID`), millisecond latency tracking, and formatted logs.
- **Async Lifespan & Cron Jobs**: FastAPI lifespan context manager managing periodic background tasks (e.g. heartbeat uptime reporter).
- **Uniform Error Envelopes**: Consistent JSON error schemas for HTTP exceptions (404), validation failures (422), and sanitized unhandled server errors (500).
- **Container & Helm Ready**: Multi-stage hardened Alpine Dockerfile using `uv`, plus a Helm chart with configurable liveness and readiness probes.
- **Automated Test Suite**: Pytest suite validating probe behavior, authentication matrices, endpoint responses, and error handlers.

---

## Project Structure

```text
.
├── Dockerfile                   # Multi-stage hardened container build using uv
├── compose.yml                  # Local containerized testing
├── mise.toml                    # Tool versions and developer task runner
├── hk.pkl                       # Pre-commit / hook configuration (hk)
├── chart/                       # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml              # Kubernetes deployment values & env vars
│   └── templates/
│       ├── deployment.yaml      # Deployment manifest with probes & env
│       └── service.yaml         # NodePort service manifest
└── src/                         # Application source code
    ├── pyproject.toml           # Dependencies and dev tools
    ├── main.py                  # App entrypoint and create_app factory
    ├── api/                     # Outbound API clients (e.g., OIDC JWKS)
    ├── auth/                    # Auth strategies (none, basic, oidc)
    ├── controllers/             # Business logic handlers
    ├── cron/                    # Periodic background tasks (heartbeat)
    ├── endpoints/               # FastAPI routers (health, user, config, test)
    ├── logger/                  # Structured console logger
    ├── startup/                 # Middleware, CORS, errors, and settings
    └── tests/                   # Pytest test suite
```

---

## Configuration Reference

Configuration is managed via Pydantic `BaseSettings` reading from environment variables or `.env` files.

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | `string` | `"skeleton-fast-api"` | Application identifier |
| `APP_ENV` | `string` | `"dev"` | Deployment stage (`dev`, `staging`, `prod`, `test`) |
| `DEBUG` | `boolean` | `false` | Enable verbose debugging and stack traces |
| `HOST` | `string` | `"0.0.0.0"` | Bind network interface address |
| `PORT` | `integer` | `8000` | Application bind port |
| `ALLOWED_ORIGINS` | `json list` | `'["*"]'` | CORS allowed origins |
| `AUTH_MODE` | `string` | `"none"` | Active auth mode: `none`, `basic`, or `oidc` |
| `BASIC_AUTH_USERNAME` | `string` | `"admin"` | Username when `AUTH_MODE=basic` |
| `BASIC_AUTH_PASSWORD` | `string` | `"admin"` | Password when `AUTH_MODE=basic` |
| `OIDC_ISSUER_URL` | `string` | `""` | OIDC issuer URL for JWKS discovery |
| `OIDC_CLIENT_ID` | `string` | `""` | Expected token audience / client ID |
| `OIDC_ALGORITHMS` | `json list` | `'["RS256"]'` | Permitted JWT signature algorithms |
| `OIDC_SSL` | `boolean` | `true` | Verify SSL certificates during JWKS fetch |
| `LOG_LEVEL` | `string` | `"INFO"` | Minimum logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `LOG_MODE` | `string` | `"none"` | Log sink (`none` for console stdout) |
| `CRON_ENABLED` | `boolean` | `true` | Enable background scheduled tasks |
| `CRON_HEARTBEAT_INTERVAL` | `integer` | `60` | Interval in seconds between heartbeat runs |

---

## Quickstart & Local Development

### Prerequisites

- [mise](https://mise.jdx.dev/) (recommended tool manager)
- [uv](https://docs.astral.sh/uv/) (Python package and virtual environment manager)
- [Docker](https://www.docker.com/)

### Install Dependencies

```bash
cd src
uv sync
```

### Run Locally

```bash
cd src
uv run fastapi dev main.py --port 8000
```

### Run Tests

Run the test suite using `mise`:

```bash
mise run test
```

Or directly with `uv`:

```bash
cd src
uv run pytest -v
```

### Run Code Quality & Lint Checks

```bash
mise run check
```

Runs formatting, license checks, YAML linting, Helm validation, and pre-commit checks via `hk`.

### Run via Docker Compose

```bash
mise run compose
```

---

## Kubernetes & Helm

The chart is located in `chart/`.

### Lint Chart

```bash
helm lint chart/
```

### Render Templates

```bash
helm template fast-api chart/
```

### Probes

- **Liveness**: `GET /health/live` (confirms process uptime).
- **Readiness**: `GET /health/ready` (confirms app readiness and settings loading).
