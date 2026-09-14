# Home.Media Architecture Inventory (Pre-Refactoring Phase 1)

## Core Components
- **FastAPI Core (`core/app/main.py`)**:
  - Central orchestrator, API server, HTTP/WebSocket reverse-proxy (`core/app/api/proxy.py`).
  - Contains routes for Auth, System settings, Plugins management, and Internal SDK callbacks.
  - Serves compiled React Admin UI.
  - Lifecycle: Reads autostart plugins from DB and launches them using `PluginManager`. Runs an asynchronous healthcheck loop in the background.

- **Plugin Manager (`core/app/services/plugin_manager.py`)**:
  - Handles the `.hm` zip extraction (with basic zip-slip check).
  - Bootstraps virtual environments (`venv`) and installs `requirements.txt`.
  - Dynamically assigns ports (`_get_free_port()`).
  - Manages processes (`subprocess.Popen` and `psutil`).
  - Stores running processes in an in-memory dictionary `self.running_processes`.

- **Database (`core/app/database.py`, `core/app/models/`)**:
  - SQLAlchemy ORM with SQLite (development) or PostgreSQL (production) support.
  - Models: `User` (Auth), `Plugin` (State and metadata), `PluginConfig` (Plugin-specific key-values including secrets), `SystemSetting` (Global settings), `ActivityLog` (Audit trail).
  - Migrations managed by Alembic.

- **Admin UI (`admin/src/`)**:
  - React (Vite) Single Page Application styled with Tailwind CSS.
  - Handles initial setup, login, dashboard (plugin list & stats), system settings, plugin configuration, logs, and embedded plugin web interfaces via IFrame.

- **Plugins (`plugins/`)**:
  - Encapsulated `.hm` files containing Python source, `manifest.json`, `requirements.txt`, and optionally a React frontend (`web/`).
  - **SDK (`plugin_sdk.py`)**: Embedded into plugins at runtime; wraps FastAPI to provide auto-registration, config fetching from Core, and routing.
  - **Telegram Bot**: Acts as a hub, dynamically querying other plugins for inline menus via `/api/internal/plugins`.
  - **Torrents**: qBittorrent wrapper with polling and remote control via its own `web/index.html`.
  - **Home Assistant**: Connects to HA API, syncs entities, provides UI for custom Telegram groups and inline menus.

## Infrastructure & Lifecycle Flows
- **Docker (`Dockerfile`, `docker-entrypoint.sh`)**:
  - Two-stage build: compiles frontend first, then builds the Python container.
  - Generates `SECRET_KEY` on first boot if missing, runs Alembic migrations, starts Uvicorn.
- **Authentication (`core/app/api/auth.py`)**:
  - JWT tokens stored in HttpOnly cookies. BCrypt password hashing.
  - Initial setup creates the first admin user.
- **Plugin Installation (`core/app/api/plugins.py`)**:
  - Direct, synchronous blocking endpoint.
  - Extracts zip -> Parses manifest -> Installs dependencies -> Registers to DB -> Starts candidate -> Validates health.
- **Plugin Proxies (`core/app/api/proxy.py`)**:
  - Both standard HTTP and WebSocket proxying supported, validating user cookies before forwarding to the internal plugin port.
