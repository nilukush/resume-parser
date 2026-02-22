"""
Database configuration and session management.

This module sets up the SQLAlchemy async engine, session factory,
and provides dependency injection for FastAPI routes.
"""
import os

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Check if we're running Alembic migrations
# If so, skip engine initialization to avoid async/sync conflicts
IS_RUNNING_MIGRATION = os.getenv("ALEMBIC_RUNNING", "false").lower() == "true"


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    All database models should inherit from this class to be
    included in the SQLAlchemy metadata and schema generation.
    """

    pass


class DatabaseManager:
    """
    Database connection manager.

    This class manages the database engine and session factory,
    providing a centralized way to handle database connections.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            database_url: Optional database URL. If not provided,
                         uses the URL from settings.
        """
        self._database_url = database_url or settings.DATABASE_URL
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def engine(self) -> AsyncEngine:
        """
        Get or create the database engine.

        Returns:
            AsyncEngine: The SQLAlchemy async engine instance.

        Raises:
            RuntimeError: If the engine has not been initialized.
        """
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. Call init_engine() first."
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Get or create the session factory.

        Returns:
            async_sessionmaker: The session factory for creating sessions.

        Raises:
            RuntimeError: If the session factory has not been initialized.
        """
        if self._session_factory is None:
            raise RuntimeError(
                "Session factory not initialized. Call init_engine() first."
            )
        return self._session_factory

    def init_engine(
        self,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
    ) -> AsyncEngine:
        """
        Initialize the database engine and session factory.

        Args:
            echo: If True, log all SQL statements.
            pool_size: The size of the connection pool.
            max_overflow: The max overflow size of the pool.
            pool_pre_ping: If True, test connections before using.

        Returns:
            AsyncEngine: The initialized engine instance.
        """
        engine_kwargs = {
            "echo": echo,
            "pool_pre_ping": pool_pre_ping,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
        }

        # Use NullPool for testing to avoid connection issues
        if settings.is_testing:
            engine_kwargs["poolclass"] = NullPool

        self._engine = create_async_engine(self._database_url, **engine_kwargs)

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        return self._engine

    async def close(self) -> None:
        """Close the database engine and dispose of all connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for getting a database session.

        Yields:
            AsyncSession: A database session that will be automatically closed.

        Example:
            async with db_manager.get_session() as session:
                result = await session.execute(query)
        """
        if self._session_factory is None:
            raise RuntimeError(
                "Session factory not initialized. Call init_engine() first."
            )

        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
db_manager = DatabaseManager()

# Create the engine and session factory (skip during migrations)
# During Alembic migrations, we only need the Base metadata, not the engine
if not IS_RUNNING_MIGRATION:
    engine = db_manager.init_engine(echo=settings.is_development)
    AsyncSessionLocal = db_manager.session_factory
else:
    engine = None  # Not used during migrations
    AsyncSessionLocal = None  # Not used during migrations


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for FastAPI routes.

    This function provides a database session to FastAPI route handlers.
    The session is automatically closed after the request is processed.

    Yields:
        AsyncSession: A database session for use in route handlers.

    Example:
        @app.get("/resumes")
        async def list_resumes(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Resume))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database.

    This function creates all database tables. In production,
    use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the database connection."""
    await db_manager.close()
