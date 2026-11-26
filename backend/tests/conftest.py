"""
Pytest configuration and shared fixtures for database tests.
"""
import os
import sys
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, Plant
from app.auth import get_current_user_id
from app.database import get_db

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

TEST_USER_ID = "test-user-123"
TEST_JWT_SECRET = "test-secret-key"

# Monkey-patch Plant creation to include user_id automatically in tests
# This must be done BEFORE any fixtures create Plant instances
_original_plant_init = Plant.__init__

def _patched_plant_init(self, **kwargs):
    # Set user_id to test user if not explicitly provided
    if 'user_id' not in kwargs:
        kwargs['user_id'] = TEST_USER_ID
    _original_plant_init(self, **kwargs)

Plant.__init__ = _patched_plant_init


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Session:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def test_client(db_engine):
    """Create a test client with dependency overrides for auth and database."""
    from app.main import app
    
    # Create session factory for test database
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def override_get_current_user_id(authorization=None):
        # Return test user ID without requiring real authentication
        return TEST_USER_ID
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    
    client = TestClient(app)
    yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_token():
    """Create a test JWT token for authentication."""
    payload = {
        "sub": TEST_USER_ID,
        "email": "test@example.com",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
    return token


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Create authorization headers with test token."""
    return {"Authorization": f"Bearer {auth_token}"}


