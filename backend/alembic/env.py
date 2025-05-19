# backend/alembic/env.py
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- Custom Setup ---
# Add the 'app' directory to the Python path so Alembic can find your modules
# This assumes your 'alembic' directory is directly inside 'backend/'
# and 'app' is also directly inside 'backend/'.
# Adjust if your project structure is different.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(project_root, "app"))
# --- End Custom Setup ---


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Custom Setup for Database URL and Metadata ---
# Import your Base model and settings
# This will make Base.metadata aware of all your models
from app.db.base import Base
from app.core.config import settings

# Set the database URL from your application settings
# This overrides the sqlalchemy.url from alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# The target_metadata should point to your Base.metadata
target_metadata = Base.metadata
# --- End Custom Setup ---


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
        # Include naming convention for offline mode if needed
        # This ensures that constraint names are generated consistently
        # when creating SQL scripts without a live DB connection.
        # This is important if you use tools that generate SQL from migrations.
        render_as_batch=True, # Often needed for SQLite, good to have for others
        # The naming_convention from Base.metadata should ideally be picked up,
        # but explicitly setting it here can be a safeguard.
        # See also: https://alembic.sqlalchemy.org/en/latest/batch.html
        # And: https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure
        # metadata=target_metadata # Already set via target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create an engine from the config (which now includes our DATABASE_URL)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), # Gets the [alembic] section
        prefix="sqlalchemy.", # Looks for keys like sqlalchemy.url, sqlalchemy.poolclass
        poolclass=pool.NullPool, # Use NullPool for migration engine; we don't need pooling here
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include naming convention for online mode as well
            # This ensures consistency when Alembic compares models to the DB.
            render_as_batch=True, # Again, useful for SQLite, generally safe
            # compare_type=True, # Detects column type changes
            # compare_server_default=True, # Detects server default changes
            # The naming_convention should be picked up from target_metadata.
            # metadata=target_metadata # Already set via target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()