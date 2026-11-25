"""
API routes for the Smart Plant Care system.

Organized by resource:
- Plants
- Devices
- Sensor readings and ingestion
- Watering
- Alerts
- Analytics
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app import schemas, models
from app.services import WateringService, AlertService
from app.security import authenticate_device

# Create routers
router = APIRouter(prefix="/api/v1", tags=["api"])

# ============================================================================
# Plant Endpoints
# ============================================================================


@router.post("/plants", response_model=schemas.PlantResponse, status_code=201, tags=["plants"])
def create_plant(plant: schemas.PlantCreate, db: Session = Depends(get_db)):
    """Create a new plant."""
    db_plant = models.Plant(**plant.dict())
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
):
    """Retrieve all plants with pagination."""
    query = db.query(models.Plant)
    if active_only:
        query = query.filter(models.Plant.is_active == True)
    return query.offset(skip).limit(limit).all()


@router.get("/plants/{plant_id}", response_model=schemas.PlantResponse, tags=["plants"])
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific plant."""
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("/plants/{plant_id}", response_model=schemas.PlantResponse, tags=["plants"])
def update_plant(
    plant_id: int,
    plant_update: schemas.PlantUpdate,
    db: Session = Depends(get_db),
):
    """Update plant configuration."""
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    update_data = plant_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plant, key, value)

    plant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plant)
    return plant


@router.delete("/plants/{plant_id}", status_code=204, tags=["plants"])
def delete_plant(plant_id: int, db: Session = Depends(get_db)):
    """Delete a plant and all associated data."""
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    db.delete(plant)  # Cascade delete handled by database
    db.commit()


# ============================================================================
# Device Endpoints
# ============================================================================


@router.post("/devices", response_model=schemas.DeviceResponse, status_code=201, tags=["devices"])
def register_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    """Register a new device."""
    # Verify plant exists
    plant = db.query(models.Plant).filter(models.Plant.id == device.plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

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
):
    """Retrieve devices with optional filtering."""
    query = db.query(models.Device)
    if plant_id:
        query = query.filter(models.Device.plant_id == plant_id)
    if status:
        query = query.filter(models.Device.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/devices/{device_id}", response_model=schemas.DeviceResponse, tags=["devices"])
def get_device(device_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific device."""
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/devices/{device_id}", response_model=schemas.DeviceResponse, tags=["devices"])
def update_device(
    device_id: int,
    device_update: schemas.DeviceUpdate,
    db: Session = Depends(get_db),
):
    """Update device configuration."""
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update_data = device_update.dict(exclude_unset=True)

    if "plant_id" in update_data:
        # Verify new plant exists
        plant = db.query(models.Plant).filter(models.Plant.id == update_data["plant_id"]).first()
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")

    for key, value in update_data.items():
        setattr(device, key, value)

    device.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


@router.delete("/devices/{device_id}", status_code=204, tags=["devices"])
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a device."""
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()


# ============================================================================
# Sensor Ingestion Endpoints
# ============================================================================


@router.post("/sensor-readings", response_model=schemas.SensorReadingResponse, status_code=201, tags=["sensors"])
def ingest_sensor_reading(
    reading: schemas.SensorReadingCreate,
    db: Session = Depends(get_db),
):
    """
    Ingest a sensor reading from a device.

    This endpoint requires device authentication via device_id.
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
    return db_reading


@router.get("/sensor-readings/plant/{plant_id}", response_model=List[schemas.SensorReadingResponse], tags=["sensors"])
def get_plant_sensor_readings(
    plant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Retrieve sensor readings for a plant."""
    # Verify plant exists
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

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
def get_latest_sensor_readings(plant_id: int, db: Session = Depends(get_db)):
    """Retrieve latest sensor readings for a plant."""
    # Verify plant exists
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

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
# Watering Endpoints
# ============================================================================


@router.post("/watering/decision/{plant_id}", response_model=schemas.WateringDecisionResponse, tags=["watering"])
def evaluate_watering_decision(
    plant_id: int,
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Evaluate if a plant is eligible for watering."""
    service = WateringService(db)
    decision, _ = service.evaluate_watering_eligibility(plant_id, device_id)
    return decision[0]


@router.post("/watering/execute/{plant_id}", response_model=schemas.VirtualWateringResponse, status_code=201, tags=["watering"])
def execute_virtual_watering(
    plant_id: int,
    device_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Execute a virtual watering operation."""
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
):
    """Retrieve watering history for a plant."""
    # Verify plant exists
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

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
def get_watering_summary(plant_id: int, db: Session = Depends(get_db)):
    """Retrieve watering summary for a plant."""
    # Verify plant exists
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

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
# Alert Endpoints
# ============================================================================


@router.get("/alerts", response_model=List[schemas.AlertResponse], tags=["alerts"])
def list_alerts(
    plant_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Retrieve alerts with optional filtering."""
    query = db.query(models.Alert)
    if plant_id:
        query = query.filter(models.Alert.plant_id == plant_id)
    if status:
        query = query.filter(models.Alert.status == status)
    if severity:
        query = query.filter(models.Alert.severity == severity)
    return query.order_by(models.Alert.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/alerts/{alert_id}", response_model=schemas.AlertResponse, tags=["alerts"])
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific alert."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}", response_model=schemas.AlertResponse, tags=["alerts"])
def update_alert(
    alert_id: int,
    alert_update: schemas.AlertUpdate,
    db: Session = Depends(get_db),
):
    """Update alert status."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
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
# Analytics Endpoints
# ============================================================================


@router.get("/analytics/plant/{plant_id}", response_model=schemas.PlantAnalyticsResponse, tags=["analytics"])
def get_plant_analytics(plant_id: int, db: Session = Depends(get_db)):
    """Retrieve comprehensive analytics for a plant."""
    # Verify plant exists
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

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
def get_system_summary(db: Session = Depends(get_db)):
    """Retrieve system-wide analytics summary."""
    total_plants = db.query(func.count(models.Plant.id)).scalar()
    active_plants = db.query(func.count(models.Plant.id)).filter(models.Plant.is_active == True).scalar()

    total_devices = db.query(func.count(models.Device.id)).scalar()
    active_devices = db.query(func.count(models.Device.id)).filter(models.Device.status == "active").scalar()

    total_readings = db.query(func.count(models.SensorReading.id)).scalar()
    total_watering_events = db.query(func.count(models.WateringEvent.id)).scalar()

    active_alerts = db.query(func.count(models.Alert.id)).filter(models.Alert.status == "active").scalar()

    critical_alerts = db.query(func.count(models.Alert.id)).filter(models.Alert.severity == "critical").scalar()

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
