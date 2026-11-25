"""
Tests for database models and relationships.
"""
import sys
import os
from datetime import datetime

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Plant, Device, SensorReading, WateringEvent, Alert


class TestPlant:
    """Tests for Plant model."""

    def test_create_plant(self, db_session: Session):
        """Test creating a plant."""
        plant = Plant(
            name="Tomato Plant",
            species="Solanum lycopersicum",
            moisture_threshold_min=30.0,
            moisture_threshold_max=80.0,
            is_active=True,
        )
        db_session.add(plant)
        db_session.commit()

        retrieved = db_session.query(Plant).filter(Plant.name == "Tomato Plant").first()
        assert retrieved is not None
        assert retrieved.name == "Tomato Plant"
        assert retrieved.species == "Solanum lycopersicum"
        assert retrieved.is_active is True

    def test_plant_timestamps(self, db_session: Session):
        """Test plant creation and update timestamps."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        assert plant.created_at is not None
        assert plant.updated_at is not None
        assert isinstance(plant.created_at, datetime)

    def test_plant_moisture_constraints(self, db_session: Session):
        """Test moisture threshold constraints."""
        # Valid plant
        plant = Plant(
            name="Valid Plant",
            moisture_threshold_min=20.0,
            moisture_threshold_max=80.0,
        )
        db_session.add(plant)
        db_session.commit()
        assert plant.id is not None

    def test_plant_active_index(self, db_session: Session):
        """Test plant query by active status."""
        plant1 = Plant(name="Active Plant", is_active=True)
        plant2 = Plant(name="Inactive Plant", is_active=False)
        db_session.add_all([plant1, plant2])
        db_session.commit()

        active_plants = db_session.query(Plant).filter(Plant.is_active == True).all()
        assert len(active_plants) == 1
        assert active_plants[0].name == "Active Plant"


class TestDevice:
    """Tests for Device model."""

    def test_create_device(self, db_session: Session):
        """Test creating a device associated with a plant."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(
            device_id="sensor_001",
            plant_id=plant.id,
            status="active",
        )
        db_session.add(device)
        db_session.commit()

        retrieved = db_session.query(Device).filter(Device.device_id == "sensor_001").first()
        assert retrieved is not None
        assert retrieved.plant_id == plant.id
        assert retrieved.status == "active"

    def test_device_unique_constraint(self, db_session: Session):
        """Test device_id uniqueness constraint."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device1 = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device1)
        db_session.commit()

        device2 = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_device_plant_relationship(self, db_session: Session):
        """Test device-to-plant relationship."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        # Reload to test relationship
        retrieved_device = db_session.query(Device).filter(Device.device_id == "sensor_001").first()
        assert retrieved_device.plant.name == "Test Plant"

    def test_device_cascade_delete(self, db_session: Session):
        """Test that deleting a plant cascades to devices."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        plant_id = plant.id
        db_session.delete(plant)
        db_session.commit()

        # Device should be deleted
        devices = db_session.query(Device).filter(Device.plant_id == plant_id).all()
        assert len(devices) == 0


class TestSensorReading:
    """Tests for SensorReading model."""

    def test_create_sensor_reading(self, db_session: Session):
        """Test creating a sensor reading."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=65.5,
            temperature=22.3,
            humidity=58.0,
        )
        db_session.add(reading)
        db_session.commit()

        retrieved = db_session.query(SensorReading).first()
        assert retrieved.soil_moisture == 65.5
        assert retrieved.temperature == 22.3
        assert retrieved.humidity == 58.0

    def test_sensor_reading_constraints(self, db_session: Session):
        """Test sensor reading percentage constraints."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        # Valid reading
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=50.0,
            humidity=50.0,
        )
        db_session.add(reading)
        db_session.commit()
        assert reading.id is not None

    def test_sensor_reading_timestamp_index(self, db_session: Session):
        """Test querying sensor readings by timestamp."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=50.0,
        )
        db_session.add(reading)
        db_session.commit()

        # Query by device and timestamp
        readings = (
            db_session.query(SensorReading)
            .filter(SensorReading.device_id == device.id)
            .all()
        )
        assert len(readings) == 1


class TestWateringEvent:
    """Tests for WateringEvent model."""

    def test_create_watering_event(self, db_session: Session):
        """Test creating a watering event."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        event = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            duration_seconds=120,
            trigger_reason="automatic",
            status="completed",
        )
        db_session.add(event)
        db_session.commit()

        retrieved = db_session.query(WateringEvent).first()
        assert retrieved.duration_seconds == 120
        assert retrieved.trigger_reason == "automatic"
        assert retrieved.status == "completed"

    def test_watering_event_plant_only(self, db_session: Session):
        """Test watering event with plant but no device."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        event = WateringEvent(
            plant_id=plant.id,
            device_id=None,
            trigger_reason="manual",
            status="completed",
        )
        db_session.add(event)
        db_session.commit()

        retrieved = db_session.query(WateringEvent).first()
        assert retrieved.plant_id == plant.id
        assert retrieved.device_id is None

    def test_watering_event_cascade(self, db_session: Session):
        """Test watering event cascade delete when device deleted."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        event = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            trigger_reason="automatic",
        )
        db_session.add(event)
        db_session.commit()

        device_id = device.id
        db_session.delete(device)
        db_session.commit()

        # Event should still exist but device_id should be NULL
        events = db_session.query(WateringEvent).filter(WateringEvent.device_id == device_id).all()
        assert len(events) == 0


class TestAlert:
    """Tests for Alert model."""

    def test_create_alert(self, db_session: Session):
        """Test creating an alert."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Soil moisture is too low",
            status="active",
        )
        db_session.add(alert)
        db_session.commit()

        retrieved = db_session.query(Alert).first()
        assert retrieved.alert_type == "dry"
        assert retrieved.severity == "warning"
        assert retrieved.status == "active"

    def test_alert_device_only(self, db_session: Session):
        """Test device-only alert."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        device = Device(device_id="sensor_001", plant_id=plant.id)
        db_session.add(device)
        db_session.commit()

        alert = Alert(
            device_id=device.id,
            alert_type="offline",
            severity="critical",
            message="Device offline",
            status="active",
        )
        db_session.add(alert)
        db_session.commit()

        retrieved = db_session.query(Alert).first()
        assert retrieved.device_id == device.id
        assert retrieved.plant_id is None

    def test_alert_resolution(self, db_session: Session):
        """Test alert resolution."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Soil moisture is too low",
            status="active",
        )
        db_session.add(alert)
        db_session.commit()

        # Resolve the alert
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        db_session.commit()

        retrieved = db_session.query(Alert).first()
        assert retrieved.status == "resolved"
        assert retrieved.resolved_at is not None


class TestRelationships:
    """Integration tests for model relationships."""

    def test_plant_with_multiple_devices(self, db_session: Session):
        """Test a plant with multiple devices."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        devices = [
            Device(device_id="sensor_001", plant_id=plant.id),
            Device(device_id="sensor_002", plant_id=plant.id),
        ]
        db_session.add_all(devices)
        db_session.commit()

        retrieved_plant = db_session.query(Plant).filter(Plant.name == "Test Plant").first()
        assert len(retrieved_plant.devices) == 2

    def test_full_plant_ecosystem(self, db_session: Session):
        """Test a complete plant ecosystem with all related entities."""
        # Create plant
        plant = Plant(name="Tomato", species="Solanum lycopersicum", is_active=True)
        db_session.add(plant)
        db_session.commit()

        # Create device
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.commit()

        # Create sensor reading
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=55.0,
            temperature=22.0,
            humidity=60.0,
        )
        db_session.add(reading)
        db_session.commit()

        # Create watering event
        event = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            duration_seconds=120,
            trigger_reason="automatic",
        )
        db_session.add(event)
        db_session.commit()

        # Create alert
        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Low moisture",
        )
        db_session.add(alert)
        db_session.commit()

        # Verify relationships
        retrieved_plant = db_session.query(Plant).filter(Plant.name == "Tomato").first()
        assert len(retrieved_plant.devices) == 1
        assert len(retrieved_plant.sensor_readings) == 1
        assert len(retrieved_plant.watering_events) == 1
        assert len(retrieved_plant.alerts) == 1
