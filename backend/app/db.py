# backend/app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

def build_database_url() -> str:
    # 1) если уже задано — используем
    url = os.getenv("DATABASE_URL")
    print(f"Using DATABASE_URL: {url}")
    if url:
        return url

    # 2) иначе собираем из POSTGRES_* c дефолтами
    user = os.getenv("POSTGRES_USER", "dupes")
    pwd = os.getenv("POSTGRES_PASSWORD", "dupes")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "dupes")

    url = f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{dbname}"
    # 3) сохраним в окружение текущего процесса (и дочерних), чтобы alembic/env.py тоже увидел
    os.environ["DATABASE_URL"] = url
    return url

DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
