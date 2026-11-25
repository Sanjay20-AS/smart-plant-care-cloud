"""
User-scoped database query utilities.

Provides helper functions to query resources owned by a specific user,
ensuring data isolation and enforcing user ownership.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Plant, Device, SensorReading, WateringEvent, Alert


def get_user_plants(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Plant]:
    """Get all plants owned by a user."""
    return (
        db.query(Plant)
        .filter(Plant.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_plant_by_id(db: Session, plant_id: int, user_id: str) -> Optional[Plant]:
    """Get a specific plant by ID, ensuring user ownership."""
    return db.query(Plant).filter(
        and_(Plant.id == plant_id, Plant.user_id == user_id)
    ).first()


def get_user_devices(db: Session, user_id: str, plant_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Device]:
    """Get all devices for a user, optionally filtered by plant."""
    query = db.query(Device).join(Plant).filter(Plant.user_id == user_id)
    if plant_id:
        query = query.filter(Device.plant_id == plant_id)
    return query.offset(skip).limit(limit).all()


def get_user_device_by_id(db: Session, device_id: int, user_id: str) -> Optional[Device]:
    """Get a specific device by ID, ensuring user ownership through plant."""
    return db.query(Device).join(Plant).filter(
        and_(Device.id == device_id, Plant.user_id == user_id)
    ).first()


def get_user_sensor_readings(db: Session, user_id: str, plant_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[SensorReading]:
    """Get all sensor readings for a user's plants."""
    query = db.query(SensorReading).join(Plant).filter(Plant.user_id == user_id)
    if plant_id:
        query = query.filter(SensorReading.plant_id == plant_id)
    return query.offset(skip).limit(limit).all()


def get_user_latest_reading(db: Session, user_id: str, plant_id: int) -> Optional[SensorReading]:
    """Get the latest sensor reading for a user's plant."""
    return db.query(SensorReading).join(Plant).filter(
        and_(
            SensorReading.plant_id == plant_id,
            Plant.user_id == user_id
        )
    ).order_by(SensorReading.reading_timestamp.desc()).first()


def get_user_watering_events(db: Session, user_id: str, plant_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[WateringEvent]:
    """Get all watering events for a user's plants."""
    query = db.query(WateringEvent).join(Plant).filter(Plant.user_id == user_id)
    if plant_id:
        query = query.filter(WateringEvent.plant_id == plant_id)
    return query.offset(skip).limit(limit).all()


def get_user_alerts(db: Session, user_id: str, plant_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Alert]:
    """Get all alerts for a user's plants."""
    query = db.query(Alert).join(Plant).filter(Plant.user_id == user_id)
    if plant_id:
        query = query.filter(Alert.plant_id == plant_id)
    return query.offset(skip).limit(limit).all()


def get_user_alert_by_id(db: Session, alert_id: int, user_id: str) -> Optional[Alert]:
    """Get a specific alert by ID, ensuring user ownership through plant."""
    return db.query(Alert).join(Plant).filter(
        and_(Alert.id == alert_id, Plant.user_id == user_id)
    ).first()
