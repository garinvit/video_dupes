# backend/alembic/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
import sys
import pathlib

# Добавляем путь к backend/, чтобы импортировать app.*
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
APP_DIR = BASE_DIR / "app"
sys.path.append(str(BASE_DIR))
sys.path.append(str(APP_DIR.parent))

# Импортирует Base и одновременно триггерит сборку DATABASE_URL из POSTGRES_*
from app.db import Base, DATABASE_URL  # noqa
config = context.config

# Установим URL для Alembic из окружения (которое уже заполнили в app.db)
database_url = os.getenv("DATABASE_URL", DATABASE_URL)
if not database_url:
    raise RuntimeError("DATABASE_URL is not set and could not be constructed")
config.set_main_option("sqlalchemy.url", database_url)

# Логи
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
