"""
Pydantic schemas for request and response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# ============================================================================
# Plant Schemas
# ============================================================================

class PlantBase(BaseModel):
    """Base plant schema with shared fields."""
    name: str = Field(..., min_length=1, max_length=255)
    species: Optional[str] = Field(None, max_length=255)
    moisture_threshold_min: float = Field(default=30.0, ge=0, le=100)
    moisture_threshold_max: float = Field(default=80.0, ge=0, le=100)
    is_active: bool = Field(default=True)

    @validator("moisture_threshold_max")
    def validate_thresholds(cls, v, values):
        if "moisture_threshold_min" in values:
            if v < values["moisture_threshold_min"]:
                raise ValueError("moisture_threshold_max must be >= moisture_threshold_min")
        return v


class PlantCreate(PlantBase):
    """Schema for creating a new plant."""
    pass


class PlantUpdate(BaseModel):
    """Schema for updating a plant."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    species: Optional[str] = Field(None, max_length=255)
    moisture_threshold_min: Optional[float] = Field(None, ge=0, le=100)
    moisture_threshold_max: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None

    @validator("moisture_threshold_max")
    def validate_thresholds(cls, v, values):
        if v is not None and "moisture_threshold_min" in values and values["moisture_threshold_min"] is not None:
            if v < values["moisture_threshold_min"]:
                raise ValueError("moisture_threshold_max must be >= moisture_threshold_min")
        return v


class PlantResponse(PlantBase):
    """Schema for plant response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Device Schemas
# ============================================================================

class DeviceBase(BaseModel):
    """Base device schema."""
    device_id: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="active")


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""
    plant_id: int


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    status: Optional[str] = None
    plant_id: Optional[int] = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""
    id: int
    plant_id: int
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceAuthResponse(BaseModel):
    """Schema for device authentication response."""
    device_key: str = Field(description="Authentication key for sensor ingestion")
    expires_at: Optional[datetime] = None


# ============================================================================
# Sensor Reading Schemas
# ============================================================================

class SensorReadingBase(BaseModel):
    """Base sensor reading schema."""
    soil_moisture: float = Field(..., ge=0, le=100)
    temperature: Optional[float] = None
    humidity: Optional[float] = Field(None, ge=0, le=100)


class SensorReadingCreate(SensorReadingBase):
    """Schema for creating a sensor reading."""
    device_id: str = Field(..., min_length=1, max_length=100)
    timestamp: Optional[datetime] = None

    @validator("temperature")
    def validate_temperature(cls, v):
        if v is not None and (v < -50 or v > 60):
            raise ValueError("temperature must be between -50 and 60 Celsius")
        return v


class SensorReadingResponse(SensorReadingBase):
    """Schema for sensor reading response."""
    id: int
    device_id: int
    plant_id: int
    reading_timestamp: datetime

    class Config:
        from_attributes = True


class LatestSensorReadingsResponse(BaseModel):
    """Schema for latest sensor readings of a plant."""
    plant_id: int
    latest_moisture: Optional[float]
    latest_temperature: Optional[float]
    latest_humidity: Optional[float]
    last_reading_timestamp: Optional[datetime]
    reading_count: int


# ============================================================================
# Watering Schemas
# ============================================================================

class WateringDecisionResponse(BaseModel):
    """Schema for watering decision response."""
    eligible: bool
    reason: str
    plant_id: int
    device_id: Optional[int]
    current_moisture: Optional[float]
    moisture_threshold: float
    decision_timestamp: datetime
    cooldown_remaining_minutes: Optional[int] = None
    daily_limit_remaining: Optional[int] = None


class WateringEventCreate(BaseModel):
    """Schema for creating a watering event."""
    plant_id: int
    device_id: Optional[int] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    trigger_reason: str = Field(default="manual")


class WateringEventResponse(BaseModel):
    """Schema for watering event response."""
    id: int
    plant_id: int
    device_id: Optional[int]
    duration_seconds: Optional[int]
    trigger_reason: str
    status: str
    event_timestamp: datetime

    class Config:
        from_attributes = True


class VirtualWateringResponse(BaseModel):
    """Schema for virtual watering execution response."""
    success: bool
    event_id: Optional[int]
    duration_seconds: Optional[int]
    message: str
    decision: WateringDecisionResponse


class WateringHistoryResponse(BaseModel):
    """Schema for watering history summary."""
    plant_id: int
    total_events: int
    last_watering_timestamp: Optional[datetime]
    recent_watering_count_24h: int
    next_eligible_time: Optional[datetime]


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertBase(BaseModel):
    """Base alert schema."""
    alert_type: str = Field(..., max_length=100)
    severity: str = Field(...)
    message: str


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    plant_id: Optional[int] = None
    device_id: Optional[int] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    status: Optional[str] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    id: int
    plant_id: Optional[int]
    device_id: Optional[int]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Analytics Schemas
# ============================================================================

class PlantAnalyticsResponse(BaseModel):
    """Schema for plant analytics summary."""
    plant_id: int
    plant_name: str
    latest_moisture: Optional[float]
    latest_temperature: Optional[float]
    latest_humidity: Optional[float]
    last_reading_timestamp: Optional[datetime]
    reading_count: int
    recent_readings_24h: int
    device_count: int
    active_devices: int
    recent_watering_count: int
    last_watering_timestamp: Optional[datetime]
    alert_count_active: int
    alert_count_critical: int


class SystemSummaryResponse(BaseModel):
    """Schema for system-wide summary."""
    total_plants: int
    active_plants: int
    total_devices: int
    active_devices: int
    total_readings: int
    total_watering_events: int
    active_alerts: int
    critical_alerts: int


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    status_code: int
