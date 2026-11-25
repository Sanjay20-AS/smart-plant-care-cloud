"""
Tests for business logic services.
"""
import sys
import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Plant, Device, SensorReading, WateringEvent, Alert
from app.services import WateringService, AlertService


class TestWateringService:
    """Tests for watering decision engine."""

    def test_evaluate_eligibility_no_plant(self, db_session: Session):
        """Test evaluation with non-existent plant."""
        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(999)
        assert decision[0].eligible is False
        assert "not found" in decision[0].reason

    def test_evaluate_eligibility_inactive_plant(self, db_session: Session):
        """Test evaluation with inactive plant."""
        plant = Plant(name="Test Plant", is_active=False)
        db_session.add(plant)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "inactive" in decision[0].reason

    def test_evaluate_eligibility_no_device(self, db_session: Session):
        """Test evaluation with no active device."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "No active device" in decision[0].reason

    def test_evaluate_eligibility_no_sensor_data(self, db_session: Session):
        """Test evaluation with no sensor data."""
        plant = Plant(name="Test Plant", is_active=True)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add_all([plant, device])
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "No sensor data" in decision[0].reason

    def test_evaluate_eligibility_old_sensor_data(self, db_session: Session):
        """Test evaluation with stale sensor data."""
        plant = Plant(name="Test Plant", is_active=True)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        old_time = datetime.utcnow() - timedelta(hours=2)
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,
            reading_timestamp=old_time,
        )
        db_session.add_all([plant, device, reading])
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "too old" in decision[0].reason

    def test_evaluate_eligibility_moisture_above_threshold(self, db_session: Session):
        """Test evaluation when moisture is above threshold."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=50.0,  # Above threshold
        )
        db_session.add_all([plant, device, reading])
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "above threshold" in decision[0].reason

    def test_evaluate_eligibility_cooldown_active(self, db_session: Session):
        """Test evaluation with cooldown period active."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,  # Below threshold
        )
        # Recent watering
        watering = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            status="completed",
            event_timestamp=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add_all([plant, device, reading, watering])
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "Cooldown" in decision[0].reason

    def test_evaluate_eligibility_daily_limit_reached(self, db_session: Session):
        """Test evaluation with daily watering limit reached."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,
        )

        # Create 3 watering events today
        now = datetime.utcnow()
        for i in range(3):
            watering = WateringEvent(
                plant_id=plant.id,
                device_id=device.id,
                status="completed",
                event_timestamp=now - timedelta(hours=i * 13),
            )
            db_session.add(watering)

        db_session.add_all([plant, device, reading])
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "Daily watering limit" in decision[0].reason

    def test_evaluate_eligibility_eligible(self, db_session: Session):
        """Test evaluation when plant is eligible for watering."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,  # Below threshold
        )
        db_session.add_all([plant, device, reading])
        db_session.commit()

        service = WateringService(db_session)
        decision, moisture = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is True
        assert decision[0].current_moisture == 20.0
        assert moisture == 20.0

    def test_execute_virtual_watering_eligible(self, db_session: Session):
        """Test virtual watering execution when eligible."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,
        )
        db_session.add_all([plant, device, reading])
        db_session.commit()

        service = WateringService(db_session)
        success, event_id, message = service.execute_virtual_watering(plant.id)

        assert success is True
        assert event_id is not None
        assert "completed" in message

        # Verify event was created
        event = db_session.query(WateringEvent).filter(WateringEvent.id == event_id).first()
        assert event is not None
        assert event.status == "completed"

    def test_execute_virtual_watering_ineligible(self, db_session: Session):
        """Test virtual watering when ineligible."""
        plant = Plant(name="Test Plant", is_active=False)
        db_session.add(plant)
        db_session.commit()

        service = WateringService(db_session)
        success, event_id, message = service.execute_virtual_watering(plant.id)

        assert success is False
        assert event_id is None
        assert "inactive" in message


class TestAlertService:
    """Tests for alert service."""

    def test_create_alert(self, db_session: Session):
        """Test creating an alert."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.commit()

        service = AlertService(db_session)
        alert = service.create_alert(
            alert_type="dry",
            severity="warning",
            message="Low moisture detected",
            plant_id=plant.id,
        )

        assert alert.id is not None
        assert alert.alert_type == "dry"
        assert alert.status == "active"

    def test_acknowledge_alert(self, db_session: Session):
        """Test acknowledging an alert."""
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

        service = AlertService(db_session)
        updated_alert = service.acknowledge_alert(alert.id)

        assert updated_alert.status == "acknowledged"

    def test_resolve_alert(self, db_session: Session):
        """Test resolving an alert."""
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

        service = AlertService(db_session)
        updated_alert = service.resolve_alert(alert.id)

        assert updated_alert.status == "resolved"
        assert updated_alert.resolved_at is not None

    def test_get_duplicate_alert_exists(self, db_session: Session):
        """Test checking for duplicate active alert."""
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

        service = AlertService(db_session)
        duplicate = service.get_duplicate_alert("dry", plant_id=plant.id)

        assert duplicate is not None
        assert duplicate.id == alert.id

    def test_get_duplicate_alert_not_active(self, db_session: Session):
        """Test that resolved alerts are not considered duplicates."""
        plant = Plant(name="Test Plant", is_active=True)
        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Low moisture",
            status="resolved",
        )
        db_session.add_all([plant, alert])
        db_session.commit()

        service = AlertService(db_session)
        duplicate = service.get_duplicate_alert("dry", plant_id=plant.id)

        assert duplicate is None
