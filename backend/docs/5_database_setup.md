# Phase 2 — Database and Alembic Setup

This completes the missing database infrastructure for the Phase 2 model plan. PostgreSQL remains the persistent source of truth, while Redis and WebSockets come in later phases. 

## Required structure

```text
backend/
├── alembic.ini
├── pyproject.toml
│
└── src/
    └── chatterlite_backend/
        ├── core/
        │   ├── config.py
        │   └── database.py
        │
        ├── models/
        │   ├── __init__.py
        │   ├── base.py
        │   ├── enums.py
        │   ├── user.py
        │   ├── conversation.py
        │   ├── conversation_member.py
        │   ├── message.py
        │   └── notification.py
        │
        └── db/
            ├── __init__.py
            └── migrations/
                ├── env.py
                ├── script.py.mako
                └── versions/
```

---

# 1. Install database dependencies

```bash
poetry add sqlalchemy asyncpg alembic
```

You need:

```text
SQLAlchemy    ORM and database engine
asyncpg       Async PostgreSQL driver
Alembic       Database migrations
```

---

# 2. `core/config.py` requirement

Your settings must contain a PostgreSQL URL using the async driver:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChatterLite"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres"
        "@localhost:5432/chatterlite"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Your `.env` should contain:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatterlite
```

The important part is:

```text
postgresql+asyncpg
```

Not:

```text
postgresql
```

---

# 3. `models/base.py`

Alembic needs one shared `Base.metadata` containing every database model.

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": (
        "fk_%(table_name)s_"
        "%(column_0_name)s_"
        "%(referred_table_name)s"
    ),
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention=NAMING_CONVENTION,
    )
```

## Why the naming convention matters

Without it, PostgreSQL may create random constraint names.

For example:

```text
users_username_key
messages_sender_id_fkey
```

With the convention, constraint names become predictable:

```text
uq_users_username
fk_messages_sender_id_users
pk_messages
```

This makes Alembic upgrades and downgrades more reliable.

Every model must import the same `Base`:

```python
from chatterlite_backend.models.base import Base
```

Never create another `DeclarativeBase` inside an individual model.

---

# 4. `core/database.py`

Create:

```text
src/chatterlite_backend/core/database.py
```

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from chatterlite_backend.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides one database session
    for one request.

    It does not automatically commit successful operations.
    Services must explicitly call session.commit().
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise


async def close_database() -> None:
    """
    Dispose the SQLAlchemy connection pool during
    application shutdown.
    """

    await engine.dispose()
```

---

## How `get_db()` works

A route uses it like this:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chatterlite_backend.core.database import get_db


router = APIRouter()


@router.get("/example")
async def example(
    db: AsyncSession = Depends(get_db),
):
    return {
        "message": "Database session available",
    }
```

Flow:

```text
Request arrives
→ database session opens
→ route/service uses session
→ response finishes
→ database session closes
```

You should explicitly commit write operations:

```python
db.add(user)

await db.commit()
await db.refresh(user)
```

Do not commit inside `get_db()`. The service controls transaction boundaries.

---

# 5. Initialize Alembic

Run this from the backend root:

```bash
poetry run alembic init src/chatterlite_backend/db/migrations
```

This creates:

```text
alembic.ini

src/chatterlite_backend/db/migrations/
├── README
├── env.py
├── script.py.mako
└── versions/
```

Also create:

```text
src/chatterlite_backend/db/__init__.py
```

It can remain empty:

```python
# Database package.
```

---

# 6. Configure `alembic.ini`

Open the generated root-level file:

```text
alembic.ini
```

Make sure the main section contains:

```ini
[alembic]

script_location = src/chatterlite_backend/db/migrations

prepend_sys_path = ./src

path_separator = os

sqlalchemy.url =
```

The full database URL does not need to be written in `alembic.ini`.

Leave this empty:

```ini
sqlalchemy.url =
```

The URL will be loaded from your Pydantic settings inside `env.py`.

This prevents database credentials from being duplicated or committed.

---

# 7. Import every model

Alembic cannot discover models merely because the files exist.

Your `models/__init__.py` must import them.

Create:

```text
src/chatterlite_backend/models/__init__.py
```

```python
from chatterlite_backend.models.conversation import Conversation
from chatterlite_backend.models.conversation_member import (
    ConversationMember,
)
from chatterlite_backend.models.message import Message
from chatterlite_backend.models.notification import Notification
from chatterlite_backend.models.user import User


__all__ = [
    "User",
    "Conversation",
    "ConversationMember",
    "Message",
    "Notification",
]
```

These imports register all model tables inside:

```python
Base.metadata
```

Without these imports, Alembic may generate an empty migration:

```python
def upgrade() -> None:
    pass
```

That is one of the most common Alembic mistakes.

---

# 8. Replace Alembic `env.py`

Replace:

```text
src/chatterlite_backend/db/migrations/env.py
```

with:

```python
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from chatterlite_backend.core.config import settings
from chatterlite_backend.models.base import Base

# Import the models package so every model is registered
# inside Base.metadata before Alembic autogenerate runs.
import chatterlite_backend.models  # noqa: F401


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


database_url = str(settings.database_url)

# Alembic uses ConfigParser internally.
# Escaping percent signs prevents interpolation errors
# if a database password contains "%".
config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.

    Alembic generates SQL using only the configured URL
    and model metadata.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(
    connection: Connection,
) -> None:
    """
    Configure Alembic using the synchronous connection
    provided through AsyncConnection.run_sync().
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Create an asynchronous SQLAlchemy engine and run
    Alembic migrations against PostgreSQL.
    """

    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations,
        )

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()

else:
    asyncio.run(
        run_migrations_online()
    )
```

---

# 9. Why `env.py` imports the models package

This line is essential:

```python
import chatterlite_backend.models  # noqa: F401
```

Import flow:

```text
env.py
→ imports chatterlite_backend.models
→ models/__init__.py imports every model
→ every table registers with Base.metadata
→ Alembic compares Base.metadata with PostgreSQL
```

Without it:

```text
Model files exist
but Python never imports them
therefore Base.metadata appears empty
```

Alembic cannot detect code it has never loaded.

---

# 10. Create the initial migration

After all five models are complete:

```bash
poetry run alembic revision \
    --autogenerate \
    -m "create initial chat models"
```

On Windows PowerShell, use one line:

```powershell
poetry run alembic revision --autogenerate -m "create initial chat models"
```

Alembic creates something like:

```text
src/chatterlite_backend/db/migrations/versions/
└── 1a2b3c4d5e6f_create_initial_chat_models.py
```

---

# 11. Review the generated migration

Do not immediately run it without reading it.

The migration should contain table creation for:

```text
users
conversations
conversation_members
messages
notifications
```

The upgrade should contain operations resembling:

```python
def upgrade() -> None:
    op.create_table(
        "users",
        ...
    )

    op.create_table(
        "conversations",
        ...
    )

    op.create_table(
        "conversation_members",
        ...
    )

    op.create_table(
        "messages",
        ...
    )

    op.create_table(
        "notifications",
        ...
    )
```

The downgrade should drop them in reverse dependency order:

```python
def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("messages")
    op.drop_table("conversation_members")
    op.drop_table("conversations")
    op.drop_table("users")
```

Do not manually rearrange tables unless Alembic generated an incorrect dependency order.

---

# 12. Apply the migration

```bash
poetry run alembic upgrade head
```

Expected result:

```text
Running upgrade -> revision_id, create initial chat models
```

---

# 13. Verify the current migration

```bash
poetry run alembic current
```

You should see:

```text
revision_id (head)
```

View migration history:

```bash
poetry run alembic history
```

---

# 14. Test downgrade and upgrade

Before building the next phase, test that rollback works.

Downgrade one revision:

```bash
poetry run alembic downgrade -1
```

Upgrade again:

```bash
poetry run alembic upgrade head
```

This verifies both methods in the migration:

```python
upgrade()
downgrade()
```

---

# 15. Application lifecycle integration

Your FastAPI application should dispose of the engine during shutdown.

In `main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from chatterlite_backend.core.database import (
    close_database,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic will go here later.
    yield

    await close_database()


app = FastAPI(
    title="ChatterLite",
    lifespan=lifespan,
)
```

Do not use this inside the application:

```python
Base.metadata.create_all()
```

Once Alembic is configured, database schema changes should go through migrations:

```text
Change models
→ generate migration
→ review migration
→ run migration
```

Not:

```text
Change models
→ create_all()
```

---

# 16. Standard workflow for future model changes

Whenever you change a model:

```bash
poetry run alembic revision --autogenerate -m "describe the model change"
```

Review the migration, then:

```bash
poetry run alembic upgrade head
```

Example:

```bash
poetry run alembic revision --autogenerate -m "add last message to conversations"

poetry run alembic upgrade head
```

Never edit an old migration that has already been applied in a shared or production environment.

Create a new migration instead.

---

# Final Phase 2 database setup checklist

```text
✅ SQLAlchemy installed
✅ asyncpg installed
✅ Alembic installed
✅ Shared Base created
✅ Naming convention configured
✅ Async engine created
✅ Async session factory created
✅ get_db dependency created
✅ Alembic initialized
✅ alembic.ini configured
✅ Database URL loaded from settings
✅ All models imported
✅ target_metadata configured
✅ Async env.py configured
✅ Initial migration generated
✅ Migration reviewed
✅ Migration upgraded
✅ Downgrade tested
✅ create_all() not used
```
