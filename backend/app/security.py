"""
Device-level security and authentication for sensor ingestion.
User ownership and authorization checks.

Modules:
- Device authentication for sensor ingestion
- User ownership verification for protected resources
- JWT token verification (see auth.py for detailed JWT handling)
"""
import secrets
import hashlib
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import Device, Plant


# Device API Key length
DEVICE_KEY_LENGTH = 32


def generate_device_key() -> str:
    """Generate a secure random key for device authentication."""
    return secrets.token_urlsafe(DEVICE_KEY_LENGTH)


def hash_device_key(key: str) -> str:
    """Hash a device key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_device_key(provided_key: str, stored_hash: str) -> bool:
    """Verify a provided key against its hash."""
    return hashlib.sha256(provided_key.encode()).hexdigest() == stored_hash


def authenticate_device(db: Session, device_id: str, auth_key: Optional[str] = None) -> Optional[Device]:
    """
    Authenticate a device for sensor ingestion.

    For now, authentication is based on device_id presence in the database.
    In production, auth_key should be validated against a stored hash.

    Args:
        db: Database session
        device_id: Device identifier from request
        auth_key: Optional authentication key (future use)

    Returns:
        Device object if authenticated, None otherwise
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return None

    # Device must be active
    if device.status != "active":
        return None

    # Auth key validation can be added here when implemented
    # For now, device_id presence is sufficient

    return device


# ============================================================================
# User Ownership Verification
# ============================================================================


def verify_plant_ownership(db: Session, plant_id: int, user_id: str) -> Plant:
    """
    Verify that a plant belongs to the authenticated user.
    
    Args:
        db: Database session
        plant_id: ID of the plant to verify
        user_id: Authenticated user's ID
    
    Returns:
        Plant object if owned by user
    
    Raises:
        HTTPException (403) if plant is not owned by user or not found
        HTTPException (404) if plant doesn't exist
    """
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    
    # Allow access if user_id is None (legacy/unowned) or matches
    if plant.user_id is not None and plant.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this plant")
    
    return plant


def verify_device_ownership(db: Session, device_id: int, user_id: str) -> Device:
    """
    Verify that a device (and its plant) belongs to the authenticated user.
    
    Args:
        db: Database session
        device_id: ID of the device to verify
        user_id: Authenticated user's ID
    
    Returns:
        Device object if owned by user
    
    Raises:
        HTTPException (403) if device is not owned by user or not found
        HTTPException (404) if device doesn't exist
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if device's plant is owned by user
    verify_plant_ownership(db, device.plant_id, user_id)
    
    return device

