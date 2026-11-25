"""
Database configuration and session management.

Supports:
- PostgreSQL for production (via Supabase)
- SQLite for local development and testing
"""
import sys
import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# Determine database configuration
DATABASE_URL = settings.DATABASE_URL

# SQLite-specific configuration for local development
if DATABASE_URL.startswith("sqlite"):
    # Use in-memory or file-based SQLite
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool
else:
    # PostgreSQL configuration
    connect_args = {}
    poolclass = None

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    poolclass=poolclass,
    echo=settings.DEBUG,  # Log SQL statements in debug mode
)

# Configure SQLite to enforce foreign key constraints
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints to get a database session.
    Usage in FastAPI route:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    This should be called once during application startup.
    However, migrations via Alembic are the preferred method for production.
    """
    from app.models import Base
    Base.metadata.create_all(bind=engine)


def get_engine():
    """Get the database engine."""
    return engine


def get_session_local():
    """Get the SessionLocal factory."""
    return SessionLocal
