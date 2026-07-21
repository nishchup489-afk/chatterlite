from collections.abc import AsyncGenerator 

from sqlalchemy.ext.asyncio import (
    AsyncEngine , 
    AsyncSession , 
    async_sessionmaker,
    create_async_engine
)

from chatterlite.core.config import Settings 


# B E S  | Base , Engine , Session.  Base in base.py , Engine and Session next. 


engine : AsyncEngine = create_async_engine(
    Settings.database_url , 
    echo=False ,               # Do not print every SQL query in the terminal.
    pool_pre_ping=True         # Check stale connection
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine , 
    class_=AsyncSession,  
    expire_on_commit=False, # After committing, keep your Python object data available.
    autoflush=False, # Do not automatically send pending changes to PostgreSQL before every query.
    autocommit=False # SQLAlchemy will not automatically save your changes.
)


async def get_db() -> AsyncGenerator[AsyncSession , None] :  # This function gives one database session to one FastAPI request.
    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise


async def close_database() -> None:
    await engine.dispose()