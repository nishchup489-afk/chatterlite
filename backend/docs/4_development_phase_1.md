We’ll build Phase 1 as **eight checkpoints**, testing after every checkpoint:

```text
1. FastAPI application shell       ← start here
2. Configuration
3. Async PostgreSQL
4. Redis
5. Alembic
6. Logging
7. Error handling
8. Clerk authentication
```

Do not connect everything at once. That is how debugging turns into archaeological excavation. 😭

# Checkpoint 1 — FastAPI application shell

## 1. Enter or create the project

From:

```powershell
C:\Users\nishc\Documents\chatterlite
```

Check whether the project already exists:

```powershell
Test-Path .\backend\pyproject.toml
```

### When it returns `True`

```powershell
cd backend
```

### When it returns `False`

```powershell
poetry new backend --name chatterlite_backend
cd backend
```

Poetry uses the `src/` layout by default, and `--name chatterlite_backend` lets the folder remain `backend` while the Python package gets the correct application name. ([Poetry][1])

Your structure should currently resemble:

```text
backend/
├── pyproject.toml
├── README.md
├── src/
│   └── chatterlite_backend/
│       └── __init__.py
└── tests/
    └── __init__.py
```

---

## 2. Attach your real Python installation

Inside `backend`:

```powershell
$pythonPath = (py -c "import sys; print(sys.executable)").Trim()

poetry config virtualenvs.in-project true --local
poetry env use $pythonPath
```

Verify:

```powershell
poetry run python --version
poetry env info --path
```

Expected:

```text
Python 3.14.4
```

The environment path should end with:

```text
backend\.venv
```

Using an in-project `.venv` makes VS Code interpreter selection much easier.

---

## 3. Install only the first dependencies

```powershell
poetry add "fastapi[standard]" pydantic-settings
poetry add --group dev pytest
```

For now:

* `fastapi[standard]` gives us FastAPI, the development server, and CLI.
* `pydantic-settings` loads typed configuration from `.env`.
* `pytest` will be used for testing.

FastAPI’s current documentation uses the `fastapi dev` command for local development. ([FastAPI][2])

Do **not** install PostgreSQL, Redis, Alembic, or Clerk yet. We will add each when its code exists.

---

# Checkpoint 2 — Create the application structure

Run this in PowerShell from `backend`:

```powershell
$directories = @(
    "src/chatterlite_backend/core",
    "src/chatterlite_backend/api",
    "src/chatterlite_backend/api/routes"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$files = @(
    "src/chatterlite_backend/core/__init__.py",
    "src/chatterlite_backend/api/__init__.py",
    "src/chatterlite_backend/api/routes/__init__.py"
)

foreach ($file in $files) {
    New-Item -ItemType File -Force -Path $file | Out-Null
}
```

Your current structure:

```text
src/chatterlite_backend/
├── __init__.py
├── main.py
├── core/
│   ├── __init__.py
│   └── config.py
└── api/
    ├── __init__.py
    ├── router.py
    └── routes/
        ├── __init__.py
        └── health.py
```

---

# Checkpoint 3 — Configuration

Create:

```text
src/chatterlite_backend/core/config.py
```

```python
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "ChatterLite API"
    app_version: str = "0.1.0"

    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@lru_cache
def get_settings() -> Settings:
    """
    Build the Settings object once and reuse it.

    Without caching, every call could reread the environment file.
    """

    return Settings()
```

## What this does

Instead of scattering configuration around:

```python
debug = True
database_url = "..."
redis_url = "..."
```

we keep it inside one typed object:

```python
settings = get_settings()

print(settings.app_name)
print(settings.debug)
```

---

# Checkpoint 4 — Environment files

Create `.env`:

```env
APP_NAME=ChatterLite API
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=true

API_V1_PREFIX=/api/v1

CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

Create `.env.example`:

```env
APP_NAME=ChatterLite API
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=true

API_V1_PREFIX=/api/v1

CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

They are identical now because we have no secrets yet.

Later:

```text
.env          → real secrets
.env.example  → fake placeholders safe for GitHub
```

---

## Add `.gitignore`

Create or update `.gitignore`:

```gitignore
# Environment variables
.env

# Poetry virtual environment
.venv/

# Python
__pycache__/
*.py[cod]
*.pyd

# Testing and tooling
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

Never commit `.env`.

---

# Checkpoint 5 — Health route

Create:

```text
src/chatterlite_backend/api/routes/health.py
```

```python
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from chatterlite_backend.core.config import get_settings


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    application: str
    environment: str
    version: str


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API health",
)
async def health_check() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        application=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
    )
```

This route will become:

```http
GET /api/v1/health
```

It currently checks only whether FastAPI is alive.

Later it will also report:

```text
API         healthy
PostgreSQL  healthy
Redis       healthy
```

---

# Checkpoint 6 — Central API router

Create:

```text
src/chatterlite_backend/api/router.py
```

```python
from fastapi import APIRouter

from chatterlite_backend.api.routes.health import router as health_router


api_router = APIRouter()

api_router.include_router(health_router)
```

Why not include every route directly in `main.py`?

Because eventually this file will contain:

```python
api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(conversations_router)
api_router.include_router(messages_router)
api_router.include_router(notifications_router)
api_router.include_router(presence_router)
```

`main.py` should create the application, not become a junk drawer.

---

# Checkpoint 7 — FastAPI application

Create:

```text
src/chatterlite_backend/main.py
```

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatterlite_backend.api.router import api_router
from chatterlite_backend.core.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown.

    PostgreSQL and Redis startup/shutdown logic will be added here later.
    """

    # Startup
    yield
    # Shutdown


def create_application() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return application


app = create_application()
```

## Why use `create_application()`?

This pattern makes the application easier to:

* Test
* Configure differently
* Start in multiple environments
* Extend without corrupting global state

## Why use `lifespan`?

Later it will control:

```text
Startup:
├── connect PostgreSQL
├── connect Redis
└── start Redis listener

Shutdown:
├── stop listener
├── close Redis
└── close PostgreSQL
```

---

# Checkpoint 8 — Run it

From the `backend` directory:

```powershell
poetry run fastapi dev src/chatterlite_backend/main.py
```

Expected terminal output will contain something similar to:

```text
Server started at http://127.0.0.1:8000
Documentation at http://127.0.0.1:8000/docs
```

Open:

```text
http://127.0.0.1:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "application": "ChatterLite API",
  "environment": "development",
  "version": "0.1.0"
}
```

Open the Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

You should see:

```text
Health
└── GET /api/v1/health
```

---

# Checkpoint 9 — Test it

Create:

```text
tests/test_health.py
```

```python
from fastapi.testclient import TestClient

from chatterlite_backend.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "application": "ChatterLite API",
        "environment": "development",
        "version": "0.1.0",
    }
```

Run:

```powershell
poetry run pytest -v
```

Expected:

```text
tests/test_health.py::test_health_check PASSED
```

---

# What you have built

```text
Browser
   │
   │ GET /api/v1/health
   ▼
FastAPI app
   │
   ▼
Central API router
   │
   ▼
Health route
   │
   ▼
Typed JSON response
```

And configuration flows like this:

```text
.env
  │
  ▼
Pydantic Settings
  │
  ▼
FastAPI application
```

That is your first legitimate foundation—not merely a random `main.py` with twenty imports.

## Next checkpoint

After this works, we wire:

```text
Async SQLAlchemy
PostgreSQL driver
AsyncSession factory
Database dependency
Database health check
```

SQLAlchemy’s current async setup uses its asyncio extension, and PostgreSQL can be connected through an async driver such as `asyncpg`; Alembic supports an async project template for migrations. ([SQLAlchemy][3])

Run the health endpoint and `pytest`, then paste the terminal output so we continue with PostgreSQL.

[1]: https://python-poetry.org/docs/cli/?utm_source=chatgpt.com "Commands | Documentation"
[2]: https://fastapi.tiangolo.com/tutorial/?utm_source=chatgpt.com "Tutorial - User Guide - FastAPI"
[3]: https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html?utm_source=chatgpt.com "Asynchronous I/O (asyncio) — SQLAlchemy 2.1 Documentation"
