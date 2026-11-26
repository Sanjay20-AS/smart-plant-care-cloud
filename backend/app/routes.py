"""
API routes with authentication for the Smart Plant Care system.

Protected endpoints require valid Supabase JWT tokens.
Unprotected endpoints remain available for device ingestion and health checks.

Organized by resource:
- Plants (protected)
- Devices (protected)
- Sensor readings and ingestion (device auth)
- Watering (protected)
- Alerts (protected)
- Analytics (protected)
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import schemas, models, services
from app.services import WateringService, AlertService
from app.security import authenticate_device, verify_plant_ownership, verify_device_ownership
from app.auth import get_current_user_id
from app.user_scope import (
    get_user_plants,
    get_user_plant_by_id,
    get_user_devices,
    get_user_device_by_id,
    get_user_sensor_readings,
    get_user_latest_reading,
    get_user_watering_events,
    get_user_alerts,
    get_user_alert_by_id,
)
from config import settings

# Create routers
router = APIRouter(prefix="/api/v1", tags=["api"])

# ============================================================================
# Plant Endpoints (Protected)
# ============================================================================


@router.post("/plants", response_model=schemas.PlantResponse, status_code=201, tags=["plants"])
def create_plant(
    plant: schemas.PlantCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new plant (requires authentication)."""
    db_plant = models.Plant(
        user_id=user_id,
        **plant.dict()
    )
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant


@router.get("/plants", response_model=List[schemas.PlantResponse], tags=["plants"])
def list_plants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve all plants for the authenticated user."""
    query = db.query(models.Plant).filter(models.Plant.user_id == user_id)
    if active_only:
        query = query.filter(models.Plant.is_active == True)
    return query.offset(skip).limit(limit).all()


@router.get("/plants/{plant_id}", response_model=schemas.PlantResponse, tags=["plants"])
def get_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve a specific plant owned by the authenticated user."""
    plant = verify_plant_ownership(db, plant_id, user_id)
    return plant


@router.put("/plants/{plant_id}", response_model=schemas.PlantResponse, tags=["plants"])
def update_plant(
    plant_id: int,
    plant_update: schemas.PlantUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update plant configuration (requires ownership)."""
    plant = verify_plant_ownership(db, plant_id, user_id)

    update_data = plant_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plant, key, value)

    plant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plant)
    return plant


@router.delete("/plants/{plant_id}", status_code=204, tags=["plants"])
def delete_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a plant and all associated data (requires ownership)."""
    plant = verify_plant_ownership(db, plant_id, user_id)
    db.delete(plant)
    db.commit()


# ============================================================================
# Device Endpoints (Protected)
# ============================================================================


@router.post("/devices", response_model=schemas.DeviceResponse, status_code=201, tags=["devices"])
def register_device(
    device: schemas.DeviceCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Register a new device for a user's plant."""
    # Verify plant exists and is owned by user
    plant = verify_plant_ownership(db, device.plant_id, user_id)

    # Check for duplicate device_id
    existing = db.query(models.Device).filter(models.Device.device_id == device.device_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device ID already exists")

    db_device = models.Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.get("/devices", response_model=List[schemas.DeviceResponse], tags=["devices"])
def list_devices(
    plant_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve devices for the authenticated user's plants."""
    return get_user_devices(db, user_id, plant_id, skip, limit)


@router.get("/devices/{device_id}", response_model=schemas.DeviceResponse, tags=["devices"])
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve a specific device owned by the authenticated user."""
    device = verify_device_ownership(db, device_id, user_id)
    return device


@router.put("/devices/{device_id}", response_model=schemas.DeviceResponse, tags=["devices"])
def update_device(
    device_id: int,
    device_update: schemas.DeviceUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update device configuration (requires ownership)."""
    device = verify_device_ownership(db, device_id, user_id)

    update_data = device_update.dict(exclude_unset=True)

    if "plant_id" in update_data:
        # Verify new plant exists and is owned by user
        verify_plant_ownership(db, update_data["plant_id"], user_id)

    for key, value in update_data.items():
        setattr(device, key, value)

    device.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


@router.delete("/devices/{device_id}", status_code=204, tags=["devices"])
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a device (requires ownership)."""
    device = verify_device_ownership(db, device_id, user_id)
    db.delete(device)
    db.commit()


# ============================================================================
# Sensor Ingestion Endpoints (Device Auth - No User Auth Required)
# ============================================================================


@router.post("/sensor-readings", response_model=schemas.SensorReadingResponse, status_code=201, tags=["sensors"])
def ingest_sensor_reading(
    reading: schemas.SensorReadingCreate,
    db: Session = Depends(get_db),
):
    """
    Ingest a sensor reading from a device.

    This endpoint requires device authentication via device_id.
    Does not require user authentication.
    
    Also generates alerts if moisture levels are outside thresholds.
    """
    # Authenticate device
    device = authenticate_device(db, reading.device_id)
    if not device:
        raise HTTPException(status_code=401, detail="Device not authenticated or not found")

    # Create sensor reading
    timestamp = reading.timestamp or datetime.utcnow()
    db_reading = models.SensorReading(
        device_id=device.id,
        plant_id=device.plant_id,
        soil_moisture=reading.soil_moisture,
        temperature=reading.temperature,
        humidity=reading.humidity,
        reading_timestamp=timestamp,
    )

    # Update device last_seen
    device.last_seen = datetime.utcnow()

    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    # Check for moisture alerts
    plant = device.plant
    alert_service = AlertService(db)
    
    # Check for low moisture (below minimum threshold)
    if reading.soil_moisture < plant.moisture_threshold_min:
        # Check if alert already exists
        existing_alert = alert_service.get_duplicate_alert(
            alert_type="dry",
            plant_id=plant.id,
            device_id=device.id
        )
        if not existing_alert:
            alert_service.create_alert(
                alert_type="dry",
                severity="warning",
                message=f"Soil moisture is {reading.soil_moisture:.1f}% (below minimum {plant.moisture_threshold_min}%)",
                plant_id=plant.id,
                device_id=device.id
            )
    
    # Check for high moisture (above maximum threshold)
    if reading.soil_moisture > plant.moisture_threshold_max:
        # Check if alert already exists
        existing_alert = alert_service.get_duplicate_alert(
            alert_type="wet",
            plant_id=plant.id,
            device_id=device.id
        )
        if not existing_alert:
            alert_service.create_alert(
                alert_type="wet",
                severity="warning",
                message=f"Soil moisture is {reading.soil_moisture:.1f}% (above maximum {plant.moisture_threshold_max}%)",
                plant_id=plant.id,
                device_id=device.id
            )
    
    return db_reading


@router.get("/sensor-readings/plant/{plant_id}", response_model=List[schemas.SensorReadingResponse], tags=["sensors"])
def get_plant_sensor_readings(
    plant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve sensor readings for a user's plant."""
    # Verify plant ownership
    verify_plant_ownership(db, plant_id, user_id)

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(models.SensorReading)
        .filter(
            models.SensorReading.plant_id == plant_id,
            models.SensorReading.reading_timestamp >= cutoff_time,
        )
        .order_by(models.SensorReading.reading_timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/sensor-readings/latest/{plant_id}", response_model=schemas.LatestSensorReadingsResponse, tags=["sensors"])
def get_latest_sensor_readings(
    plant_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve latest sensor readings for a user's plant."""
    # Verify plant ownership
    verify_plant_ownership(db, plant_id, user_id)

    latest = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.plant_id == plant_id)
        .order_by(models.SensorReading.reading_timestamp.desc())
        .first()
    )

    reading_count = db.query(func.count(models.SensorReading.id)).filter(models.SensorReading.plant_id == plant_id).scalar()

    return schemas.LatestSensorReadingsResponse(
        plant_id=plant_id,
        latest_moisture=latest.soil_moisture if latest else None,
        latest_temperature=latest.temperature if latest else None,
        latest_humidity=latest.humidity if latest else None,
        last_reading_timestamp=latest.reading_timestamp if latest else None,
        reading_count=reading_count,
    )


# ============================================================================
# Watering Endpoints (Protected)
# ============================================================================


@router.post("/watering/decision/{plant_id}", response_model=schemas.WateringDecisionResponse, tags=["watering"])
def evaluate_watering_decision(
    plant_id: int,
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Evaluate if a user's plant is eligible for watering."""
    # Verify plant ownership
    verify_plant_ownership(db, plant_id, user_id)

    service = WateringService(db)
    decision, _ = service.evaluate_watering_eligibility(plant_id, device_id)
    return decision[0]


@router.post("/watering/execute/{plant_id}", response_model=schemas.VirtualWateringResponse, status_code=201, tags=["watering"])
def execute_virtual_watering(
    plant_id: int,
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Execute a virtual watering operation for a user's plant."""
    # Verify plant ownership
    verify_plant_ownership(db, plant_id, user_id)

    service = WateringService(db)
    success, event_id, message = service.execute_virtual_watering(plant_id, device_id)

    # Get decision for response
    decision, _ = service.evaluate_watering_eligibility(plant_id, device_id)

    return schemas.VirtualWateringResponse(
        success=success,
        event_id=event_id,
        duration_seconds=120 if success else None,
        message=message,
        decision=decision[0],
    )


@router.get("/watering/history/{plant_id}", response_model=List[schemas.WateringEventResponse], tags=["watering"])
def get_watering_history(
    plant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve watering history for a user's plant."""
    # Verify plant ownership
    verify_plant_ownership(db, plant_id, user_id)

    cutoff_time = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(models.WateringEvent)
        .filter(
            models.WateringEvent.plant_id == plant_id,
            models.WateringEvent.event_timestamp >= cutoff_time,
        )
        .order_by(models.WateringEvent.event_timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/watering/summary/{plant_id}", response_model=schemas.WateringHistoryResponse, tags=["watering"])
def get_watering_summary(
    plant_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve watering summary for a user's plant."""
    # Verify plant ownership
    verify_plant_ownership(db, plant_id, user_id)

    # Total events
    total_events = db.query(func.count(models.WateringEvent.id)).filter(models.WateringEvent.plant_id == plant_id).scalar()

    # Last watering
    last_event = (
        db.query(models.WateringEvent)
        .filter(
            models.WateringEvent.plant_id == plant_id,
            models.WateringEvent.status == "completed",
        )
        .order_by(models.WateringEvent.event_timestamp.desc())
        .first()
    )

    # Recent waterings (24h)
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    recent_count = (
        db.query(func.count(models.WateringEvent.id))
        .filter(
            models.WateringEvent.plant_id == plant_id,
            models.WateringEvent.status == "completed",
            models.WateringEvent.event_timestamp >= cutoff_24h,
        )
        .scalar()
    )

    # Next eligible time (approximation based on last watering + cooldown)
    next_eligible = None
    if last_event:
        next_eligible = last_event.event_timestamp + timedelta(hours=12)

    return schemas.WateringHistoryResponse(
        plant_id=plant_id,
        total_events=total_events,
        last_watering_timestamp=last_event.event_timestamp if last_event else None,
        recent_watering_count_24h=recent_count,
        next_eligible_time=next_eligible,
    )


# ============================================================================
# Alert Endpoints (Protected)
# ============================================================================


@router.get("/alerts", response_model=List[schemas.AlertResponse], tags=["alerts"])
def list_alerts(
    plant_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve alerts for the authenticated user's plants."""
    return get_user_alerts(db, user_id, plant_id, skip, limit)


@router.get("/alerts/{alert_id}", response_model=schemas.AlertResponse, tags=["alerts"])
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve a specific alert owned by the authenticated user."""
    alert = get_user_alert_by_id(db, alert_id, user_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}", response_model=schemas.AlertResponse, tags=["alerts"])
def update_alert(
    alert_id: int,
    alert_update: schemas.AlertUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update alert status (requires ownership)."""
    alert = get_user_alert_by_id(db, alert_id, user_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert_update.status:
        alert.status = alert_update.status
        if alert_update.status == "resolved":
            alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)
    return alert


# ============================================================================
# Analytics Endpoints (Protected)
# ============================================================================


@router.get("/analytics/plant/{plant_id}", response_model=schemas.PlantAnalyticsResponse, tags=["analytics"])
def get_plant_analytics(
    plant_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve comprehensive analytics for a user's plant."""
    # Verify plant ownership
    plant = verify_plant_ownership(db, plant_id, user_id)

    # Latest reading
    latest_reading = (
        db.query(models.SensorReading)
        .filter(models.SensorReading.plant_id == plant_id)
        .order_by(models.SensorReading.reading_timestamp.desc())
        .first()
    )

    # Count metrics
    reading_count = db.query(func.count(models.SensorReading.id)).filter(models.SensorReading.plant_id == plant_id).scalar()

    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    readings_24h = (
        db.query(func.count(models.SensorReading.id))
        .filter(
            models.SensorReading.plant_id == plant_id,
            models.SensorReading.reading_timestamp >= cutoff_24h,
        )
        .scalar()
    )

    device_count = db.query(func.count(models.Device.id)).filter(models.Device.plant_id == plant_id).scalar()

    active_devices = (
        db.query(func.count(models.Device.id))
        .filter(models.Device.plant_id == plant_id, models.Device.status == "active")
        .scalar()
    )

    watering_24h = (
        db.query(func.count(models.WateringEvent.id))
        .filter(
            models.WateringEvent.plant_id == plant_id,
            models.WateringEvent.event_timestamp >= cutoff_24h,
        )
        .scalar()
    )

    last_watering = (
        db.query(models.WateringEvent)
        .filter(models.WateringEvent.plant_id == plant_id)
        .order_by(models.WateringEvent.event_timestamp.desc())
        .first()
    )

    active_alerts = (
        db.query(func.count(models.Alert.id))
        .filter(models.Alert.plant_id == plant_id, models.Alert.status == "active")
        .scalar()
    )

    critical_alerts = (
        db.query(func.count(models.Alert.id))
        .filter(models.Alert.plant_id == plant_id, models.Alert.severity == "critical")
        .scalar()
    )

    return schemas.PlantAnalyticsResponse(
        plant_id=plant_id,
        plant_name=plant.name,
        latest_moisture=latest_reading.soil_moisture if latest_reading else None,
        latest_temperature=latest_reading.temperature if latest_reading else None,
        latest_humidity=latest_reading.humidity if latest_reading else None,
        last_reading_timestamp=latest_reading.reading_timestamp if latest_reading else None,
        reading_count=reading_count,
        recent_readings_24h=readings_24h,
        device_count=device_count,
        active_devices=active_devices,
        recent_watering_count=watering_24h,
        last_watering_timestamp=last_watering.event_timestamp if last_watering else None,
        alert_count_active=active_alerts,
        alert_count_critical=critical_alerts,
    )


@router.get("/analytics/summary", response_model=schemas.SystemSummaryResponse, tags=["analytics"])
def get_system_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Retrieve analytics summary for the authenticated user's plants."""
    # Count only user's plants
    total_plants = db.query(func.count(models.Plant.id)).filter(models.Plant.user_id == user_id).scalar()
    active_plants = db.query(func.count(models.Plant.id)).filter(
        models.Plant.user_id == user_id,
        models.Plant.is_active == True
    ).scalar()

    # Count devices for user's plants
    user_plant_ids = db.query(models.Plant.id).filter(models.Plant.user_id == user_id).subquery()
    total_devices = db.query(func.count(models.Device.id)).filter(models.Device.plant_id.in_(user_plant_ids)).scalar()
    active_devices = db.query(func.count(models.Device.id)).filter(
        models.Device.plant_id.in_(user_plant_ids),
        models.Device.status == "active"
    ).scalar()

    # Count readings for user's plants
    total_readings = db.query(func.count(models.SensorReading.id)).filter(models.SensorReading.plant_id.in_(user_plant_ids)).scalar()
    total_watering_events = db.query(func.count(models.WateringEvent.id)).filter(models.WateringEvent.plant_id.in_(user_plant_ids)).scalar()

    # Count alerts for user's plants
    active_alerts = db.query(func.count(models.Alert.id)).filter(
        models.Alert.plant_id.in_(user_plant_ids),
        models.Alert.status == "active"
    ).scalar()
    critical_alerts = db.query(func.count(models.Alert.id)).filter(
        models.Alert.plant_id.in_(user_plant_ids),
        models.Alert.severity == "critical"
    ).scalar()

    return schemas.SystemSummaryResponse(
        total_plants=total_plants,
        active_plants=active_plants,
        total_devices=total_devices,
        active_devices=active_devices,
        total_readings=total_readings,
        total_watering_events=total_watering_events,
        active_alerts=active_alerts,
        critical_alerts=critical_alerts,
    )
