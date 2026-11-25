"""
Device-level security and authentication for sensor ingestion.

This module handles device-level security only. User authentication
will be integrated in a later phase via Supabase Auth.
"""
import secrets
import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Device


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
