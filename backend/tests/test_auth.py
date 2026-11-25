"""
Tests for authentication and user ownership enforcement.
"""
import os
import sys
import pytest
import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base, Plant, Device, SensorReading, WateringEvent, Alert
from app.auth import verify_jwt_token, extract_user_id_from_token, get_current_user_id
from app.security import verify_plant_ownership, verify_device_ownership
from fastapi import HTTPException

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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


# ============================================================================
# JWT Token Tests
# ============================================================================


def test_extract_user_id_from_test_token():
    """Test extracting user ID from a test JWT token."""
    # Create a test token (unsigned)
    payload = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    
    user_id = extract_user_id_from_token(token)
    assert user_id == "test-user-123"


def test_extract_user_id_from_invalid_token():
    """Test that invalid token returns None."""
    user_id = extract_user_id_from_token("invalid.token.here")
    assert user_id is None


# ============================================================================
# Plant Ownership Tests
# ============================================================================


def test_verify_plant_ownership_success(db_session):
    """Test verifying ownership of a plant that belongs to user."""
    user_id = "user-123"
    plant = Plant(
        name="Tomato",
        user_id=user_id,
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add(plant)
    db_session.commit()
    
    # Should not raise
    result = verify_plant_ownership(db_session, plant.id, user_id)
    assert result.id == plant.id
    assert result.user_id == user_id


def test_verify_plant_ownership_wrong_user(db_session):
    """Test that accessing another user's plant raises 403."""
    plant = Plant(
        name="Tomato",
        user_id="user-123",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add(plant)
    db_session.commit()
    
    # Try to access as different user
    with pytest.raises(HTTPException) as exc_info:
        verify_plant_ownership(db_session, plant.id, "user-456")
    assert exc_info.value.status_code == 403


def test_verify_plant_ownership_not_found(db_session):
    """Test that accessing non-existent plant raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        verify_plant_ownership(db_session, 999, "user-123")
    assert exc_info.value.status_code == 404


def test_verify_plant_ownership_legacy_unowned(db_session):
    """Test that plants with no user_id can be accessed by anyone."""
    plant = Plant(
        name="Tomato",
        user_id=None,  # Legacy plant without owner
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add(plant)
    db_session.commit()
    
    # Should be accessible (for backward compatibility)
    result = verify_plant_ownership(db_session, plant.id, "any-user")
    assert result.id == plant.id


# ============================================================================
# Device Ownership Tests
# ============================================================================


def test_verify_device_ownership_success(db_session):
    """Test verifying ownership of a device through its plant."""
    user_id = "user-123"
    plant = Plant(
        name="Tomato",
        user_id=user_id,
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add(plant)
    db_session.commit()
    
    device = Device(
        device_id="dev-001",
        plant_id=plant.id,
        status="active",
    )
    db_session.add(device)
    db_session.commit()
    
    # Should not raise
    result = verify_device_ownership(db_session, device.id, user_id)
    assert result.id == device.id
    assert result.plant_id == plant.id


def test_verify_device_ownership_wrong_user(db_session):
    """Test that accessing another user's device raises 403."""
    plant = Plant(
        name="Tomato",
        user_id="user-123",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add(plant)
    db_session.commit()
    
    device = Device(
        device_id="dev-001",
        plant_id=plant.id,
        status="active",
    )
    db_session.add(device)
    db_session.commit()
    
    # Try to access as different user
    with pytest.raises(HTTPException) as exc_info:
        verify_device_ownership(db_session, device.id, "user-456")
    assert exc_info.value.status_code == 403


def test_verify_device_ownership_not_found(db_session):
    """Test that accessing non-existent device raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        verify_device_ownership(db_session, 999, "user-123")
    assert exc_info.value.status_code == 404


# ============================================================================
# Multi-User Data Isolation Tests
# ============================================================================


def test_plants_isolated_by_user(db_session):
    """Test that plants are isolated between users."""
    # Create plants for different users
    plant1 = Plant(
        name="User1 Plant",
        user_id="user-1",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    plant2 = Plant(
        name="User2 Plant",
        user_id="user-2",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add_all([plant1, plant2])
    db_session.commit()
    
    # User 1 can see their plant
    user1_plants = db_session.query(Plant).filter(Plant.user_id == "user-1").all()
    assert len(user1_plants) == 1
    assert user1_plants[0].name == "User1 Plant"
    
    # User 1 cannot see user 2's plant
    user1_cannot_see = db_session.query(Plant).filter(
        Plant.user_id == "user-1",
        Plant.id == plant2.id
    ).first()
    assert user1_cannot_see is None


def test_devices_isolated_through_plants(db_session):
    """Test that devices are isolated through plant ownership."""
    # Create plants for different users
    plant1 = Plant(
        name="User1 Plant",
        user_id="user-1",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    plant2 = Plant(
        name="User2 Plant",
        user_id="user-2",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add_all([plant1, plant2])
    db_session.commit()
    
    # Create devices for each plant
    device1 = Device(device_id="dev-1", plant_id=plant1.id, status="active")
    device2 = Device(device_id="dev-2", plant_id=plant2.id, status="active")
    db_session.add_all([device1, device2])
    db_session.commit()
    
    # User 1 can see their device
    user1_devices = db_session.query(Device).join(Plant).filter(
        Plant.user_id == "user-1"
    ).all()
    assert len(user1_devices) == 1
    assert user1_devices[0].device_id == "dev-1"
    
    # User 1 cannot see user 2's device
    user1_cannot_see = db_session.query(Device).join(Plant).filter(
        Plant.user_id == "user-1",
        Device.id == device2.id
    ).first()
    assert user1_cannot_see is None


def test_sensor_readings_isolated(db_session):
    """Test that sensor readings are isolated by plant ownership."""
    # Create plants for different users
    plant1 = Plant(
        name="User1 Plant",
        user_id="user-1",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    plant2 = Plant(
        name="User2 Plant",
        user_id="user-2",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add_all([plant1, plant2])
    db_session.commit()
    
    # Create devices
    device1 = Device(device_id="dev-1", plant_id=plant1.id, status="active")
    device2 = Device(device_id="dev-2", plant_id=plant2.id, status="active")
    db_session.add_all([device1, device2])
    db_session.commit()
    
    # Create readings
    reading1 = SensorReading(
        device_id=device1.id,
        plant_id=plant1.id,
        soil_moisture=50.0,
    )
    reading2 = SensorReading(
        device_id=device2.id,
        plant_id=plant2.id,
        soil_moisture=60.0,
    )
    db_session.add_all([reading1, reading2])
    db_session.commit()
    
    # User 1 can see their readings
    user1_readings = db_session.query(SensorReading).join(Plant).filter(
        Plant.user_id == "user-1"
    ).all()
    assert len(user1_readings) == 1
    assert user1_readings[0].soil_moisture == 50.0


def test_watering_events_isolated(db_session):
    """Test that watering events are isolated by plant ownership."""
    # Create plants for different users
    plant1 = Plant(
        name="User1 Plant",
        user_id="user-1",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    plant2 = Plant(
        name="User2 Plant",
        user_id="user-2",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add_all([plant1, plant2])
    db_session.commit()
    
    # Create watering events
    event1 = WateringEvent(
        plant_id=plant1.id,
        trigger_reason="automatic",
        status="completed",
    )
    event2 = WateringEvent(
        plant_id=plant2.id,
        trigger_reason="automatic",
        status="completed",
    )
    db_session.add_all([event1, event2])
    db_session.commit()
    
    # User 1 can see their events
    user1_events = db_session.query(WateringEvent).join(Plant).filter(
        Plant.user_id == "user-1"
    ).all()
    assert len(user1_events) == 1


def test_alerts_isolated(db_session):
    """Test that alerts are isolated by plant ownership."""
    # Create plants for different users
    plant1 = Plant(
        name="User1 Plant",
        user_id="user-1",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    plant2 = Plant(
        name="User2 Plant",
        user_id="user-2",
        moisture_threshold_min=30.0,
        moisture_threshold_max=80.0,
    )
    db_session.add_all([plant1, plant2])
    db_session.commit()
    
    # Create alerts
    alert1 = Alert(
        plant_id=plant1.id,
        alert_type="dry",
        severity="warning",
        message="Plant is dry",
    )
    alert2 = Alert(
        plant_id=plant2.id,
        alert_type="dry",
        severity="warning",
        message="Plant is dry",
    )
    db_session.add_all([alert1, alert2])
    db_session.commit()
    
    # User 1 can see their alerts
    user1_alerts = db_session.query(Alert).join(Plant, isouter=True).filter(
        Plant.user_id == "user-1"
    ).all()
    assert len(user1_alerts) == 1
