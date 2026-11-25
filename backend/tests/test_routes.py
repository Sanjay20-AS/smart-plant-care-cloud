"""
Tests for API routes and endpoints.
"""
import sys
import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.models import Plant, Device, SensorReading, WateringEvent, Alert
from app.database import get_db
from tests.conftest import db_session


def get_db_override(session: Session):
    """Override get_db to use the test session."""
    def _get_db():
        yield session
    return _get_db


client = TestClient(app)


@pytest.fixture(autouse=True)
def override_get_db(db_session: Session):
    """Override FastAPI dependency to use fixture session."""
    def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()



# ============================================================================
# Plant Endpoints Tests
# ============================================================================


class TestPlantEndpoints:
    """Tests for plant management endpoints."""

    def test_create_plant(self, db_session: Session):
        """Test creating a plant."""
        response = client.post(
            "/api/v1/plants",
            json={
                "name": "Tomato",
                "species": "Solanum lycopersicum",
                "moisture_threshold_min": 30.0,
                "moisture_threshold_max": 80.0,
                "is_active": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tomato"
        assert data["id"] is not None

    def test_list_plants(self, db_session: Session):
        """Test listing plants."""
        # Create a plant directly in DB
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        response = client.get("/api/v1/plants")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_plant(self, db_session: Session):
        """Test retrieving a specific plant."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        response = client.get(f"/api/v1/plants/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plant.id
        assert data["name"] == "Test Plant"

    def test_get_plant_not_found(self):
        """Test retrieving non-existent plant."""
        response = client.get("/api/v1/plants/999")
        assert response.status_code == 404

    def test_update_plant(self, db_session: Session):
        """Test updating a plant."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        db_session.add(plant)
        db_session.commit()

        response = client.put(
            f"/api/v1/plants/{plant.id}",
            json={"moisture_threshold_min": 25.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["moisture_threshold_min"] == 25.0

    def test_delete_plant(self, db_session: Session):
        """Test deleting a plant."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()
        plant_id = plant.id

        response = client.delete(f"/api/v1/plants/{plant_id}")
        assert response.status_code == 204

        # Verify deletion
        deleted_plant = db_session.query(Plant).filter(Plant.id == plant_id).first()
        assert deleted_plant is None


# ============================================================================
# Device Endpoints Tests
# ============================================================================


class TestDeviceEndpoints:
    """Tests for device management endpoints."""

    def test_register_device(self, db_session: Session):
        """Test registering a device."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        response = client.post(
            "/api/v1/devices",
            json={
                "device_id": "sensor_001",
                "plant_id": plant.id,
                "status": "active",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["device_id"] == "sensor_001"

    def test_register_device_duplicate_id(self, db_session: Session):
        """Test registering device with duplicate ID."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        # Create first device
        response1 = client.post(
            "/api/v1/devices",
            json={
                "device_id": "sensor_001",
                "plant_id": plant.id,
                "status": "active",
            },
        )
        assert response1.status_code == 201

        # Try to create second device with same ID
        response2 = client.post(
            "/api/v1/devices",
            json={
                "device_id": "sensor_001",
                "plant_id": plant.id,
                "status": "active",
            },
        )
        assert response2.status_code == 400

    def test_list_devices(self, db_session: Session):
        """Test listing devices."""
        response = client.get("/api/v1/devices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_device(self, db_session: Session):
        """Test retrieving a specific device."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.commit()

        response = client.get(f"/api/v1/devices/{device.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == "sensor_001"

    def test_update_device_status(self, db_session: Session):
        """Test updating device status."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.commit()

        response = client.put(
            f"/api/v1/devices/{device.id}",
            json={"status": "inactive"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inactive"

    def test_delete_device(self, db_session: Session):
        """Test deleting a device."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.commit()
        device_id = device.id

        response = client.delete(f"/api/v1/devices/{device_id}")
        assert response.status_code == 204


# ============================================================================
# Sensor Ingestion Tests
# ============================================================================


class TestSensorIngestion:
    """Tests for sensor data ingestion."""

    def test_ingest_sensor_reading(self, db_session: Session):
        """Test ingesting a sensor reading."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.commit()

        response = client.post(
            "/api/v1/sensor-readings",
            json={
                "device_id": "sensor_001",
                "soil_moisture": 65.5,
                "temperature": 22.3,
                "humidity": 58.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["soil_moisture"] == 65.5
        assert data["device_id"] == device.id

    def test_ingest_reading_invalid_device(self):
        """Test ingesting reading with invalid device."""
        response = client.post(
            "/api/v1/sensor-readings",
            json={
                "device_id": "invalid_device",
                "soil_moisture": 65.5,
            },
        )
        assert response.status_code == 401

    def test_ingest_reading_invalid_moisture(self):
        """Test ingesting reading with invalid moisture."""
        response = client.post(
            "/api/v1/sensor-readings",
            json={
                "device_id": "sensor_001",
                "soil_moisture": 150.0,  # Invalid
            },
        )
        assert response.status_code == 422  # Validation error

    def test_get_plant_sensor_readings(self, db_session: Session):
        """Test retrieving plant sensor readings."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.flush()
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=65.5,
            temperature=22.3,
        )
        db_session.add(reading)
        db_session.commit()

        response = client.get(f"/api/v1/sensor-readings/plant/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["soil_moisture"] == 65.5

    def test_get_latest_sensor_readings(self, db_session: Session):
        """Test retrieving latest sensor readings."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.flush()
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=65.5,
            temperature=22.3,
        )
        db_session.add(reading)
        db_session.commit()

        response = client.get(f"/api/v1/sensor-readings/latest/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["latest_moisture"] == 65.5


# ============================================================================
# Watering Endpoints Tests
# ============================================================================


class TestWateringEndpoints:
    """Tests for watering endpoints."""

    def test_evaluate_watering_decision_eligible(self, db_session: Session):
        """Test watering decision when plant is eligible."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.flush()
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,  # Below threshold
            temperature=22.3,
        )
        db_session.add(reading)
        db_session.commit()

        response = client.post(f"/api/v1/watering/decision/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["eligible"] is True
        assert data["current_moisture"] == 20.0

    def test_evaluate_watering_decision_ineligible_no_reading(self, db_session: Session):
        """Test watering decision when no sensor data."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        response = client.post(f"/api/v1/watering/decision/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["eligible"] is False

    def test_execute_virtual_watering(self, db_session: Session):
        """Test executing virtual watering."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.flush()
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,
        )
        db_session.add(reading)
        db_session.commit()

        response = client.post(f"/api/v1/watering/execute/{plant.id}")
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] is not None

    def test_get_watering_history(self, db_session: Session):
        """Test retrieving watering history."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        event = WateringEvent(
            plant_id=plant.id,
            trigger_reason="manual",
            status="completed",
        )
        db_session.add(event)
        db_session.commit()

        response = client.get(f"/api/v1/watering/history/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_watering_summary(self, db_session: Session):
        """Test retrieving watering summary."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        response = client.get(f"/api/v1/watering/summary/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 0


# ============================================================================
# Alert Endpoints Tests
# ============================================================================


class TestAlertEndpoints:
    """Tests for alert endpoints."""

    def test_list_alerts(self, db_session: Session):
        """Test listing alerts."""
        plant = Plant(name="Test Plant", is_active=True)
        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Low moisture",
            status="active",
        )
        db_session.add_all([plant, alert])
        db_session.commit()

        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_alert(self, db_session: Session):
        """Test retrieving a specific alert."""
        plant = Plant(name="Test Plant", is_active=True)
        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Low moisture",
            status="active",
        )
        db_session.add_all([plant, alert])
        db_session.commit()

        response = client.get(f"/api/v1/alerts/{alert.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["alert_type"] == "dry"

    def test_update_alert_status(self, db_session: Session):
        """Test updating alert status."""
        plant = Plant(name="Test Plant", is_active=True)
        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Low moisture",
            status="active",
        )
        db_session.add_all([plant, alert])
        db_session.commit()

        response = client.put(
            f"/api/v1/alerts/{alert.id}",
            json={"status": "acknowledged"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"


# ============================================================================
# Analytics Endpoints Tests
# ============================================================================


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    def test_get_plant_analytics(self, db_session: Session):
        """Test retrieving plant analytics."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        response = client.get(f"/api/v1/analytics/plant/{plant.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["plant_id"] == plant.id
        assert data["plant_name"] == "Test Plant"

    def test_get_system_summary(self, db_session: Session):
        """Test retrieving system summary."""
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_plants" in data
        assert "total_devices" in data


# ============================================================================
# Health and Root Endpoints
# ============================================================================


class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
