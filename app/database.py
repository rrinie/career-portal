"""
database.py
-----------
Creates the SQLAlchemy engine, session factory, and declarative Base.
All models must inherit from Base so they are registered with the ORM.

Environment variable required:
    DATABASE_URL  e.g. postgresql://user:password@localhost:5432/career_portal
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# pool_pre_ping=True lets SQLAlchemy test connections before using them,
# which prevents "SSL connection has been closed unexpectedly" errors on
# long-lived workers.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
# autocommit=False  → we control transactions explicitly
# autoflush=False   → prevents implicit flushes that can cause confusing errors
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------------
# Every SQLAlchemy model will inherit from this Base.
Base = declarative_base()
