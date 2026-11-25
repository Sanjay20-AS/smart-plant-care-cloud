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
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "No sensor data" in decision[0].reason

    def test_evaluate_eligibility_old_sensor_data(self, db_session: Session):
        """Test evaluation with stale sensor data."""
        plant = Plant(name="Test Plant", is_active=True)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.flush()
        old_time = datetime.utcnow() - timedelta(hours=2)
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=20.0,
            reading_timestamp=old_time,
        )
        db_session.add(reading)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "too old" in decision[0].reason

    def test_evaluate_eligibility_moisture_above_threshold(self, db_session: Session):
        """Test evaluation when moisture is above threshold."""
        plant = Plant(name="Test Plant", is_active=True, moisture_threshold_min=30.0)
        db_session.add(plant)
        db_session.flush()
        device = Device(device_id="sensor_001", plant_id=plant.id, status="active")
        db_session.add(device)
        db_session.flush()
        reading = SensorReading(
            device_id=device.id,
            plant_id=plant.id,
            soil_moisture=50.0,  # Above threshold
        )
        db_session.add(reading)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "above threshold" in decision[0].reason

    def test_evaluate_eligibility_cooldown_active(self, db_session: Session):
        """Test evaluation with cooldown period active."""
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
        )
        db_session.add(reading)
        db_session.flush()
        # Recent watering
        watering = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            trigger_reason="manual",
            status="completed",
            event_timestamp=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(watering)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "Cooldown" in decision[0].reason

    def test_evaluate_eligibility_daily_limit_reached(self, db_session: Session):
        """Test evaluation with daily watering limit reached."""
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
        db_session.flush()

        # Create 3 watering events that are very old so they don't trigger cooldown
        # and they're all from "today" for counting purposes
        now = datetime.utcnow()
        # For simplicity, make all 3 events from the very start of today (00:00:01, 00:00:02, 00:00:03)
        # They'll all be old enough to pass cooldown (since they're 20+ hours old)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # The challenge is: we need them > 12h old to bypass cooldown, but < 24h old to be in today's count
        # This is only possible if "now" is > 12 hours into the day
        # Since it's 20:51, we have plenty of room
        
        # Event 1: 00:00:01 today (now - 20h 51m = well past 12h)
        watering_t1 = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            trigger_reason="automatic",
            status="completed",
            event_timestamp=today_start + timedelta(seconds=1),
        )
        db_session.add(watering_t1)
        db_session.flush()
        
        # Event 2: 00:00:02 today (also > 12h old)
        watering_t2 = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            trigger_reason="automatic",
            status="completed",
            event_timestamp=today_start + timedelta(seconds=2),
        )
        db_session.add(watering_t2)
        db_session.flush()
        
        # Event 3: 00:00:03 today (also > 12h old)
        watering_t3 = WateringEvent(
            plant_id=plant.id,
            device_id=device.id,
            trigger_reason="automatic",
            status="completed",
            event_timestamp=today_start + timedelta(seconds=3),
        )
        db_session.add(watering_t3)
        db_session.commit()

        # Now evaluate - with 3 events and max of 3, we should be ineligible
        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is False
        assert "Daily watering limit reached" in decision[0].reason
        assert decision[0].daily_limit_remaining == 0

    def test_evaluate_eligibility_eligible(self, db_session: Session):
        """Test evaluation when plant is eligible for watering."""
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
        )
        db_session.add(reading)
        db_session.commit()

        service = WateringService(db_session)
        decision, _ = service.evaluate_watering_eligibility(plant.id)
        assert decision[0].eligible is True
        assert decision[0].current_moisture == 20.0
        assert decision[1] == 20.0

    def test_execute_virtual_watering_eligible(self, db_session: Session):
        """Test virtual watering execution when eligible."""
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
        db_session.add(plant)
        db_session.flush()
        alert = Alert(
            plant_id=plant.id,
            alert_type="dry",
            severity="warning",
            message="Low moisture",
            status="active",
        )
        db_session.add(alert)
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
