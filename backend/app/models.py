"""
SQLAlchemy database models for Smart Plant Care system.

Models:
- Plant: Represents individual plants
- Device: Represents IoT devices associated with plants
- SensorReading: Stores historical sensor data
- WateringEvent: Stores watering records
- Alert: Stores system alerts
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Plant(Base):
    """Represents an individual plant."""

    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    species = Column(String(255), nullable=True, comment="Plant species or type")
    moisture_threshold_min = Column(
        Float, default=30.0, comment="Minimum soil moisture percentage for watering"
    )
    moisture_threshold_max = Column(
        Float, default=80.0, comment="Maximum safe soil moisture percentage"
    )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    devices = relationship("Device", back_populates="plant", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="plant", cascade="all, delete-orphan")
    watering_events = relationship("WateringEvent", back_populates="plant", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="plant", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("moisture_threshold_min >= 0 AND moisture_threshold_min <= 100"),
        CheckConstraint("moisture_threshold_max >= 0 AND moisture_threshold_max <= 100"),
        CheckConstraint("moisture_threshold_min <= moisture_threshold_max"),
        Index("idx_plant_active", "is_active"),
    )


class Device(Base):
    """Represents a virtual IoT device associated with a plant."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="active", comment="active, inactive, error")
    last_seen = Column(DateTime, nullable=True, comment="Last communication timestamp")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    plant = relationship("Plant", back_populates="devices")
    sensor_readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")
    watering_events = relationship("WateringEvent", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_device_id"),
        Index("idx_device_plant_id", "plant_id"),
        Index("idx_device_status", "status"),
    )


class SensorReading(Base):
    """Stores historical sensor measurements."""

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    soil_moisture = Column(Float, nullable=False, comment="Soil moisture percentage (0-100)")
    temperature = Column(Float, nullable=True, comment="Temperature in Celsius")
    humidity = Column(Float, nullable=True, comment="Relative humidity percentage (0-100)")
    reading_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    device = relationship("Device", back_populates="sensor_readings")
    plant = relationship("Plant", back_populates="sensor_readings")

    # Constraints
    __table_args__ = (
        CheckConstraint("soil_moisture >= 0 AND soil_moisture <= 100"),
        CheckConstraint("humidity >= 0 AND humidity <= 100"),
        Index("idx_sensor_device_timestamp", "device_id", "reading_timestamp"),
        Index("idx_sensor_plant_timestamp", "plant_id", "reading_timestamp"),
    )


class WateringEvent(Base):
    """Stores historical watering records."""

    __tablename__ = "watering_events"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    duration_seconds = Column(Integer, nullable=True, comment="Watering duration in seconds")
    trigger_reason = Column(
        String(100),
        nullable=False,
        comment="manual, automatic, scheduled, threshold",
    )
    status = Column(
        String(50),
        default="completed",
        comment="completed, failed, cancelled",
    )
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    plant = relationship("Plant", back_populates="watering_events")
    device = relationship("Device", back_populates="watering_events")

    # Constraints
    __table_args__ = (
        CheckConstraint("duration_seconds IS NULL OR duration_seconds >= 0"),
        Index("idx_watering_plant_timestamp", "plant_id", "event_timestamp"),
        Index("idx_watering_device_timestamp", "device_id", "event_timestamp"),
    )


class Alert(Base):
    """Stores system alerts for plants and devices."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    alert_type = Column(
        String(100),
        nullable=False,
        comment="dry, wet, low_battery, offline, error, etc.",
    )
    severity = Column(
        String(50),
        nullable=False,
        comment="info, warning, critical",
    )
    message = Column(Text, nullable=False)
    status = Column(
        String(50),
        default="active",
        comment="active, acknowledged, resolved",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    plant = relationship("Plant", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")

    # Constraints
    __table_args__ = (
        Index("idx_alert_plant_created", "plant_id", "created_at"),
        Index("idx_alert_device_created", "device_id", "created_at"),
        Index("idx_alert_status", "status"),
    )
