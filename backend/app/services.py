"""
Business logic services for the Smart Plant Care system.

Includes:
- Watering decision engine
- Alert generation and management
- Sensor data processing
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Plant, Device, SensorReading, WateringEvent, Alert
from app.schemas import WateringDecisionResponse


# ============================================================================
# Configuration Constants
# ============================================================================

# Watering cooldown in hours (minimum time between waterings)
WATERING_COOLDOWN_HOURS = 12

# Maximum watering events per day
MAX_WATERING_EVENTS_PER_DAY = 3

# Sensor data freshness requirement in minutes
SENSOR_DATA_FRESHNESS_MINUTES = 60

# Virtual watering duration in seconds
VIRTUAL_WATERING_DURATION_SECONDS = 120


# ============================================================================
# Watering Service
# ============================================================================

class WateringService:
    """Service for watering decision logic and virtual watering operations."""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_watering_eligibility(
        self, plant_id: int, device_id: Optional[int] = None
    ) -> Tuple[WateringDecisionResponse, Optional[int]]:
        """
        Evaluate if a plant is eligible for watering.

        Returns:
            Tuple of (WateringDecisionResponse, latest_moisture_percentage)
        """
        now = datetime.utcnow()

        # Fetch plant
        plant = self.db.query(Plant).filter(Plant.id == plant_id).first()
        if not plant:
            return (
                WateringDecisionResponse(
                    eligible=False,
                    reason="Plant not found",
                    plant_id=plant_id,
                    device_id=device_id,
                    current_moisture=None,
                    moisture_threshold=0,
                    decision_timestamp=now,
                ),
                None,
            ), None

        if not plant.is_active:
            return (
                WateringDecisionResponse(
                    eligible=False,
                    reason="Plant is inactive",
                    plant_id=plant_id,
                    device_id=device_id,
                    current_moisture=None,
                    moisture_threshold=plant.moisture_threshold_min,
                    decision_timestamp=now,
                ),
                None,
            ), None

        # Fetch device if specified
        if device_id:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device or device.plant_id != plant_id:
                return (
                    WateringDecisionResponse(
                        eligible=False,
                        reason="Device not found or not associated with plant",
                        plant_id=plant_id,
                        device_id=device_id,
                        current_moisture=None,
                        moisture_threshold=plant.moisture_threshold_min,
                        decision_timestamp=now,
                    ),
                    None,
                ), None
        else:
            # Get any active device for the plant
            device = (
                self.db.query(Device)
                .filter(Device.plant_id == plant_id, Device.status == "active")
                .first()
            )
            if not device:
                return (
                    WateringDecisionResponse(
                        eligible=False,
                        reason="No active device found for plant",
                        plant_id=plant_id,
                        device_id=None,
                        current_moisture=None,
                        moisture_threshold=plant.moisture_threshold_min,
                        decision_timestamp=now,
                    ),
                    None,
                ), None
            device_id = device.id

        # Get latest sensor reading
        latest_reading = (
            self.db.query(SensorReading)
            .filter(SensorReading.plant_id == plant_id)
            .order_by(SensorReading.reading_timestamp.desc())
            .first()
        )

        if not latest_reading:
            return (
                WateringDecisionResponse(
                    eligible=False,
                    reason="No sensor data available",
                    plant_id=plant_id,
                    device_id=device_id,
                    current_moisture=None,
                    moisture_threshold=plant.moisture_threshold_min,
                    decision_timestamp=now,
                ),
                None,
            ), None

        # Check sensor data freshness
        time_since_reading = now - latest_reading.reading_timestamp
        if time_since_reading > timedelta(minutes=SENSOR_DATA_FRESHNESS_MINUTES):
            return (
                WateringDecisionResponse(
                    eligible=False,
                    reason=f"Sensor data too old (> {SENSOR_DATA_FRESHNESS_MINUTES} minutes)",
                    plant_id=plant_id,
                    device_id=device_id,
                    current_moisture=latest_reading.soil_moisture,
                    moisture_threshold=plant.moisture_threshold_min,
                    decision_timestamp=now,
                ),
                None,
            ), None

        current_moisture = latest_reading.soil_moisture

        # Check moisture threshold
        if current_moisture >= plant.moisture_threshold_min:
            return (
                WateringDecisionResponse(
                    eligible=False,
                    reason=f"Soil moisture {current_moisture}% is above threshold {plant.moisture_threshold_min}%",
                    plant_id=plant_id,
                    device_id=device_id,
                    current_moisture=current_moisture,
                    moisture_threshold=plant.moisture_threshold_min,
                    decision_timestamp=now,
                ),
                None,
            ), None

        # Check daily watering limit BEFORE cooldown
        # (daily limit is a hard business rule, cooldown is a safeguard)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_waterings = (
            self.db.query(func.count(WateringEvent.id))
            .filter(
                WateringEvent.plant_id == plant_id,
                WateringEvent.event_timestamp >= today_start,
                WateringEvent.status == "completed",
            )
            .scalar()
        )

        if daily_waterings >= MAX_WATERING_EVENTS_PER_DAY:
            return (
                WateringDecisionResponse(
                    eligible=False,
                    reason=f"Daily watering limit reached ({daily_waterings}/{MAX_WATERING_EVENTS_PER_DAY})",
                    plant_id=plant_id,
                    device_id=device_id,
                    current_moisture=current_moisture,
                    moisture_threshold=plant.moisture_threshold_min,
                    decision_timestamp=now,
                    daily_limit_remaining=0,
                ),
                None,
            ), None

        # Check cooldown period
        last_watering = (
            self.db.query(WateringEvent)
            .filter(WateringEvent.plant_id == plant_id, WateringEvent.status == "completed")
            .order_by(WateringEvent.event_timestamp.desc())
            .first()
        )

        if last_watering:
            time_since_watering = now - last_watering.event_timestamp
            cooldown_minutes = WATERING_COOLDOWN_HOURS * 60
            if time_since_watering < timedelta(minutes=cooldown_minutes):
                remaining_cooldown = int(
                    (timedelta(minutes=cooldown_minutes) - time_since_watering).total_seconds() / 60
                )
                return (
                    WateringDecisionResponse(
                        eligible=False,
                        reason=f"Cooldown period active",
                        plant_id=plant_id,
                        device_id=device_id,
                        current_moisture=current_moisture,
                        moisture_threshold=plant.moisture_threshold_min,
                        decision_timestamp=now,
                        cooldown_remaining_minutes=remaining_cooldown,
                    ),
                    None,
                ), None

        # All checks passed
        return (
            WateringDecisionResponse(
                eligible=True,
                reason=f"Watering eligible - moisture {current_moisture}% below threshold {plant.moisture_threshold_min}%",
                plant_id=plant_id,
                device_id=device_id,
                current_moisture=current_moisture,
                moisture_threshold=plant.moisture_threshold_min,
                decision_timestamp=now,
                daily_limit_remaining=MAX_WATERING_EVENTS_PER_DAY - daily_waterings,
            ),
            current_moisture,
        ), None

    def execute_virtual_watering(
        self, plant_id: int, device_id: Optional[int] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Execute a virtual watering operation for an eligible plant.

        Returns:
            Tuple of (success: bool, event_id: Optional[int], message: str)
        """
        now = datetime.utcnow()

        # Evaluate eligibility
        decision_response, _ = self.evaluate_watering_eligibility(plant_id, device_id)

        if not decision_response[0].eligible:
            return False, None, decision_response[0].reason

        # Create watering event
        watering_event = WateringEvent(
            plant_id=plant_id,
            device_id=device_id,
            duration_seconds=VIRTUAL_WATERING_DURATION_SECONDS,
            trigger_reason="automatic",
            status="completed",
            event_timestamp=now,
        )

        self.db.add(watering_event)
        self.db.commit()

        return (
            True,
            watering_event.id,
            f"Virtual watering completed for {VIRTUAL_WATERING_DURATION_SECONDS}s",
        )


# ============================================================================
# Alert Service
# ============================================================================

class AlertService:
    """Service for alert generation and management."""

    def __init__(self, db: Session):
        self.db = db

    def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        plant_id: Optional[int] = None,
        device_id: Optional[int] = None,
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            plant_id=plant_id,
            device_id=device_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            status="active",
        )
        self.db.add(alert)
        self.db.commit()
        return alert

    def acknowledge_alert(self, alert_id: int) -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = "acknowledged"
            self.db.commit()
        return alert

    def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        """Resolve an alert."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            self.db.commit()
        return alert

    def get_duplicate_alert(
        self,
        alert_type: str,
        plant_id: Optional[int] = None,
        device_id: Optional[int] = None,
    ) -> Optional[Alert]:
        """Check for existing active alert of same type."""
        return (
            self.db.query(Alert)
            .filter(
                Alert.alert_type == alert_type,
                Alert.plant_id == plant_id,
                Alert.device_id == device_id,
                Alert.status.in_(["active", "acknowledged"]),
            )
            .first()
        )
