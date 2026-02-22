import os
import sys
import configparser
from logging.config import fileConfig
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(backend_dir, '.env'))

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Signal that we're running migrations to prevent async engine initialization
os.environ["ALEMBIC_RUNNING"] = "true"

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models here
from app.core.database import Base
from app.models.resume import Resume, ParsedResumeData, ResumeCorrection, ResumeShare

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get DATABASE_URL from environment, fallback to config file
database_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

# For Alembic migrations, we need to convert asyncpg to psycopg for synchronous migrations
# Alembic doesn't support async migrations directly
# Note: psycopg 3.x uses 'postgresql+psycopg://' URL
if database_url.startswith("postgresql+asyncpg://"):
    # Convert to psycopg 3.x format for sync migrations
    database_url_sync = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    # Plain postgresql:// URL, convert to use psycopg
    database_url_sync = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    database_url_sync = database_url

# IMPORTANT: Don't set this back to config if it has special characters
# ConfigParser fails on URL-encoded passwords with % and { }
# Instead, we'll pass it directly to the engine
try:
    config.set_main_option("sqlalchemy.url", database_url_sync)
except (ValueError, configparser.InterpolationError) as e:
    # If ConfigParser fails (special characters in password), skip setting it
    # The engine will use the URL directly from environment variable
    import warnings
    warnings.warn(f"Could not set URL in alembic.ini due to special characters: {e}")
    # Store in environment for run_migrations_online() to use
    os.environ["ALEMBIC_DATABASE_URL"] = database_url_sync

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Synchronous engine for Alembic migrations
    from sqlalchemy import engine_from_config

    # Check if we have a fallback URL from environment (ConfigParser failed)
    fallback_url = os.environ.get("ALEMBIC_DATABASE_URL")

    if fallback_url:
        # Create engine directly from URL (bypasses config.get_section)
        from sqlalchemy import create_engine
        connectable = create_engine(fallback_url, poolclass=pool.NullPool)
    else:
        # Use standard config-based engine creation
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
