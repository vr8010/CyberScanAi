"""
Async SQLAlchemy database engine and session setup.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Use SQLite for local dev if DATABASE_URL is not a real postgres URL
_db_url = settings.DATABASE_URL
if "localhost" in _db_url and "postgresql" in _db_url:
    # Fall back to SQLite so no Postgres install is needed locally
    _db_url = "sqlite+aiosqlite:///./securescout.db"

_is_sqlite = _db_url.startswith("sqlite")

# Async engine for FastAPI
engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    **({"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20} if not _is_sqlite else {"connect_args": {"check_same_thread": False}}),
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
