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
| `MAX_REQUEST_SIZE` | `integer` | `10485760` | Global fallback maximum request payload size in bytes (10MB) |
| `MAX_JSON_SIZE` | `integer` | `1048576` | Maximum JSON request payload size in bytes (1MB) |
| `MAX_UPLOAD_SIZE` | `integer` | `20971520` | Maximum multipart form and document upload size in bytes (20MB) |
| `CONFIG_PATH` | `string` | `""` | Optional explicit path to JSON configuration file (`config.json`) |

---

## Security & Compliance Architecture

Both OpenShift and Talos Linux prioritize workload security and least privilege, but they enforce and evaluate constraints through different mechanisms. This repository is architected to satisfy both environments without code changes.

### OpenShift Compliance (`restricted-v2` SCC)

OpenShift uses **Security Context Constraints (SCC)** to control pod permissions. Under the default `restricted-v2` SCC:
- **Arbitrary Dynamic UIDs**: OpenShift assigns a random UID from a dedicated per-namespace range (e.g., `1000670000`). Containers cannot assume a fixed UID like `1000`.
- **Root Group (GID 0)**: Files and directories required at runtime must be owned by group 0 (`chgrp -R 0`) with group read/write permissions (`chmod -R g+rwX`) so the dynamically assigned UID can access them. The base Python image (`ghcr.io/joeckr/python:3.14`) configures `/app` with GID 0 ownership.
- **Dropped Capabilities**: Drops standard root capabilities (`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETUID`, `SETGID`, `SYS_CHROOT`, etc.) and permits only unprivileged operations (and `NET_BIND_SERVICE` when needed).
- **Unprivileged Ports**: Containers must listen on non-privileged ports (> 1024), such as port `8000`.

### Talos Linux Compliance (Kubernetes PSS `restricted`)

Talos Linux is an immutable, minimal, secure-by-default Kubernetes operating system with no SSH, no interactive shell, and an immutable root filesystem. In Talos clusters:
- **Pod Security Standards (PSS)**: Workload namespaces enforce the Kubernetes **Pod Security Admission (PSA)** `restricted` profile.
- **Must Run As Non-Root**: The pod specification sets `securityContext.runAsNonRoot: true`. Containers cannot execute as UID 0.
- **Drop All Capabilities**: The container specification explicitly drops all Linux capabilities (`capabilities: drop: ["ALL"]`).
- **Disallow Privilege Escalation**: Sets `securityContext.allowPrivilegeEscalation: false` to prevent child processes from acquiring more privileges than the parent.
- **Seccomp Profile**: Pods enforce `seccompProfile: { type: RuntimeDefault }`.
- **Credential Protection**: Hardened with `automountServiceAccountToken: false` to avoid leaking Kubernetes API tokens to application containers.
- **Health Probes**: Configures HTTP liveness (`/health/live`) and readiness (`/health/ready`) probes bypassing authentication for reliable orchestrator lifecycle management.

### Rootless Build Environment Compliance

Building container images inside secure or unprivileged environments (such as rootless Podman/Buildah on developer workstations, or unprivileged Kubernetes CI runners like Tekton or Kaniko) requires that the build process itself does not rely on host `root` privileges or the legacy root-owned Docker daemon socket (`/var/run/docker.sock`).

This repository's `Dockerfile` is engineered for complete rootless build support:
- **No Host Root Required**: Multi-stage build executes and succeeds cleanly under unprivileged user namespaces without needing `sudo` or privileged container builders.
- **User Namespace Friendly Permissions**: Layer assembly relies on `uv sync` creating the virtual environment in `/app/.venv` without requiring privileged system-level package manager hooks.
- **Unprivileged Local Build**: Run `mise run build` (`podman buildx build --platform linux/amd64 -t ghcr.io/joeckr/skeleton-fast-api:test . --load`) or `mise run compose` to build locally without root escalation.

### Compliance Matrix

| Security Dimension | OpenShift (`restricted-v2` SCC) | Talos Linux (Kubernetes PSS `restricted`) | Implementation in This Repo |
|---|---|---|---|
| **Build Execution** | Rootless builder compatible | Rootless builder compatible | Builds unprivileged via rootless Podman/Buildah (`mise run build`) |
| **User ID** | Dynamic arbitrary UID (`MustRunAsRange`) | Non-root UID (`runAsNonRoot: true`) | `USER 1031` in base image + `runAsNonRoot: true` in Helm |
| **Group Permissions** | Requires GID 0 (`root`) with `g+rwX` | Compatible with GID 0 / unprivileged groups | `chgrp -R 0` & `chmod -R g+rwX` on `/app` in base image |
| **Capabilities** | Drops root caps; allows `NET_BIND_SERVICE` | Must drop `ALL` capabilities | `capabilities.drop: ["ALL"]` in Helm chart |
| **Privilege Escalation** | Prohibited | `allowPrivilegeEscalation: false` | Configured in Helm `securityContext` |
| **Seccomp Profile** | `RuntimeDefault` | `RuntimeDefault` or `Localhost` | `seccompProfile: { type: RuntimeDefault }` |
| **Service Account Token** | Optional | Recommended disabled | `automountServiceAccountToken: false` in pod spec |
| **Port Binding** | Unprivileged (> 1024) | Unprivileged (> 1024) | Listens on port `8000` |
| **Health Probes** | HTTP Probes | HTTP Probes | `/health/live` and `/health/ready` |

---

## Local Environment & Podman Setup

To ensure containerized applications and Helm charts tested locally run cleanly when deployed to OpenShift or Talos Linux, this repository is designed to be used alongside the Podman configuration in [joeckr/dotfiles](https://github.com/joeckr/dotfiles).

The dotfiles repository provides a centralized [`containers.conf`](https://github.com/joeckr/dotfiles/blob/main/containers/containers.conf) (deployed to `~/.config/containers/containers.conf`) that configures Podman to simulate OpenShift and Talos Linux runtime restrictions:

| Security Rule | Podman Configuration | Description |
|---|---|---|
| **Random UID (`MustRunAsRange`)** | `userns = "auto"` | Allocates dynamic subordinate UID/GID ranges from `/etc/subuid` and `/etc/subgid`. Containers run unprivileged without mapping host root. |
| **Drop Capabilities** | `default_capabilities = ["NET_BIND_SERVICE"]` | Drops standard root capabilities (`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETUID`, `SETGID`, `SYS_CHROOT`, etc.) and permits only `NET_BIND_SERVICE`. |
| **Disallow Privileged** | `privileged = false` | Disallows privileged container execution by default. |
| **Seccomp Profile** | `seccomp_profile = "/usr/share/containers/seccomp.json"` | Enforces the runtime default seccomp profile (`RuntimeDefault`). |
| **Namespace Isolation** | `cgroupns`, `ipcns`, `pidns`, `utsns = "private"` | Enforces private container namespaces (host namespaces are forbidden in restricted profiles). |

### macOS Podman Machine Integration

On macOS, the dotfiles installer script (`brew/podman.sh`) automates the machine lifecycle:

1. Deploys `containers/containers.conf` to `~/.config/containers/containers.conf` on the host.
2. Initializing `podman machine init` automatically mounts `~/.config/containers` into `/etc/containers` inside the Fedora CoreOS VM.
3. Automatically symlinks `/etc/containers/containers.conf` to the VM user's config (`~core/.config/containers/containers.conf`) and restarts the Podman API service so all container executions immediately enforce these constraints.

---

## Testing & Validation Process

This repository defines a 3-tier testing process to validate application logic, container security, manifest generation, and runtime compatibility from local development through to production cluster deployment.

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│ Tier 1: Local Container │ ──> │ Tier 2: Podman Play     │ ──> │ Tier 3: Talos Cluster   │
│ Fast iteration & health │     │ Validate K8s manifests  │     │ Live Helm verification  │
│ (compose.yml)           │     │ (podman play kube)      │     │ (helm install)          │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### Tier 1: Local Container Validation (`compose.yml`)

The [`compose.yml`](compose.yml) configuration builds and runs the container locally using Podman Compose:

```sh
# Build and start the container in the background
mise run compose
# or: podman compose up -d --build

# View container logs
mise run logs
# or: podman compose logs -f

# Verify liveness probe
curl -f http://localhost:8000/health/live

# Verify readiness probe
curl -f http://localhost:8000/health/ready

# Stop compose stack
mise run down
# or: podman compose down
```

**What this verifies:**
- Rootless multi-stage image build and layer assembly without host root privileges.
- Non-root user execution (`USER 1031`).
- Port binding on unprivileged port `8000`.
- Lifespan initialization, configuration parsing, structured logging, and health probe responses.

---

### Tier 2: Local Kubernetes Manifest Testing (`mise run play`)

Before deploying to an actual Kubernetes cluster, you can test the rendered Kubernetes manifests locally using Podman's built-in `play kube` feature.

```sh
# Render templates and play Kubernetes manifests locally
mise run play

# Teardown the played pod and resources
mise run downplay
```

**How `mise run play` works:**
1. Triggers the dependent task `mise run helm-template`, which executes:
   ```sh
   helm dependency build chart/
   helm template test chart/ > rendered.yaml
   ```
2. Executes `podman play kube rendered.yaml`, which:
   - Reads the multi-document Kubernetes YAML (`Deployment`, `Service`).
   - Creates a local Podman pod matching the Kubernetes `Deployment` specification.
   - Applies the pod's `securityContext` (`runAsNonRoot: true`, capabilities drop, seccomp profile).
   - Exposes container port `8000`.

**Inspecting the local play deployment:**
```sh
# View running pods created by play kube
podman pod ps

# View container status within the pod
podman ps --filter "pod=fast-api"

# Verify service health
curl -f http://localhost:8000/health/live

# Check container logs within the pod
podman logs -f fast-api-pod-fast-api
```

**Teardown:**
```sh
mise run downplay
# or: podman play kube rendered.yaml --down
```

---

### Tier 3: Cluster Deployment & Testing on Talos Linux (`mise run helm-install`)

The final phase validates the workload on a live **Talos Linux** Kubernetes cluster. This tests real-world Pod Security Admission (PSA) enforcement, network connectivity, and application startup under production constraints.

#### 1. Cluster Prerequisites & Configuration

Ensure your `kubectl` context points to your Talos cluster:
```sh
kubectl config current-context
# Example: admin@my-talos-cluster
```

Verify that the target namespace enforces the `restricted` Pod Security Standard:
```sh
kubectl get ns default --show-labels
# Should include:
# pod-security.kubernetes.io/enforce=restricted
# pod-security.kubernetes.io/enforce-version=latest
```

#### 2. Linting & Template Validation

Run the linter and inspect the generated manifests before cluster deployment:
```sh
mise run helm-lint
mise run helm-template
```

#### 3. Deploying to the Talos Cluster

Install the Helm chart release:
```sh
mise run helm-install
# or: helm install test chart/
```

#### 4. Verifying Talos PSS Compliance & Health

Check the pod status and verify that Talos Linux Pod Security Admission (PSA) allowed the pod to run:

```sh
# Check pod deployment status
kubectl get pods -l app=fast-api

# Inspect pod details and events for security policy rejections
kubectl describe pod -l app=fast-api
```

> [!TIP]
> If your namespace enforces the `restricted` Pod Security Standard and there are non-compliant settings (such as missing `runAsNonRoot` or un-dropped capabilities), `kubectl describe pod` will show warning events from the `pod-security` admission controller.

Check the application logs:
```sh
kubectl logs -l app=fast-api -f
```

Verify application endpoints via port-forwarding:
```sh
# Forward port 8000 from the cluster pod
kubectl port-forward svc/fast-api 8000:8000

# In a separate shell, test probes
curl -f http://localhost:8000/health/live
curl -f http://localhost:8000/health/ready
```

#### 5. Uninstalling from the Talos Cluster

When testing is complete, clean up the release:
```sh
mise run helm-uninstall
# or: helm uninstall test
```

---

## Local Development & Tasks

### Setup

```bash
# Install tools and git hooks
mise run install
```

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

### Available Tasks

Run tasks with `mise run <task>`:

| Task | Description | Command |
|---|---|---|
| `install` | Install tools and set up git hooks | `hk install --mise` |
| `hk` (or `check`) | Run all linters and hook checks | `hk check --all` |
| `test` | Run pytest test suite | `cd src && uv run pytest -v` |
| `compose` | Start local container stack with Podman Compose | `podman compose up -d --build` |
| `down` | Stop local Podman Compose stack | `podman compose down` |
| `logs` | View Podman Compose logs | `podman compose logs -f` |
| `play` | Test Helm chart manifests locally with Podman Play Kube | `podman play kube rendered.yaml` |
| `downplay` | Stop and remove Podman Play Kube pods | `podman play kube rendered.yaml --down` |
| `helm-dep` | Build Helm chart dependencies | `helm dependency build chart/` |
| `helm-lint` | Lint Helm chart | `helm lint chart/` |
| `helm-template` | Render Helm chart templates to `rendered.yaml` | `helm template test chart/ > rendered.yaml` |
| `helm-install` | Install Helm chart to current Kubernetes cluster | `helm install test chart/` |
| `helm-uninstall` | Uninstall Helm chart release from cluster | `helm uninstall test` |
| `build` | Build container image locally with Podman Buildx | `podman buildx build --platform linux/amd64 -t ghcr.io/joeckr/skeleton-fast-api:test . --load` |
| `trivy-fs` | Scan repository filesystem for security vulnerabilities | `trivy fs .` |
| `trivy-image` | Scan built container image with Trivy | `trivy image ghcr.io/joeckr/skeleton-fast-api:test` |

---

## Support

If you find this project useful, consider supporting my work on [Ko-fi](https://ko-fi.com/joeckr):

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/joeckr)

## License

Please refer to the `LICENSE` file for details.
