"""
JWT authentication and verification for Supabase Auth.

Provides:
- JWT token verification using JWKS (JSON Web Key Set) from Supabase
- Dependency for FastAPI to extract and verify user identity
- Token claims extraction and validation
"""
import os
import json
import httpx
import jwt
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from functools import lru_cache

from config import settings
from app.database import get_db

# Cache for JWKS keys (refresh every 24 hours)
_jwks_cache = None
_jwks_cache_time = None


async def get_jwks():
    """
    Fetch JWKS from Supabase.
    JWKS URL is: https://<SUPABASE_URL>/auth/v1/.well-known/openid-configuration
    """
    global _jwks_cache, _jwks_cache_time
    
    if _jwks_cache is not None:
        return _jwks_cache
    
    if not settings.SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Supabase URL not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch OIDC configuration first to get JWKS URL
            oidc_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/openid-configuration"
            oidc_response = await client.get(oidc_url, timeout=10)
            oidc_response.raise_for_status()
            oidc_data = oidc_response.json()
            
            jwks_url = oidc_data.get("jwks_uri")
            if not jwks_url:
                raise Exception("JWKS URI not found in OIDC configuration")
            
            # Fetch JWKS
            jwks_response = await client.get(jwks_url, timeout=10)
            jwks_response.raise_for_status()
            _jwks_cache = jwks_response.json()
            return _jwks_cache
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch JWKS: {str(e)}")


def get_public_key(token: str) -> Optional[str]:
    """
    Extract the public key from JWKS matching the token's kid (key ID).
    """
    try:
        import asyncio
        
        # For synchronous context, we need to handle async differently
        # In production, use an async endpoint or cache JWKS in memory
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    jwks = loop.run_until_complete(get_jwks())
    
    # Decode without verification to get the header
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    
    # Find matching key in JWKS
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            # Reconstruct public key from JWK
            if key.get("kty") == "RSA":
                from cryptography.hazmat.primitives.serialization import load_pem_public_key
                from cryptography.hazmat.backends import default_backend
                from jose import jwk
                
                # Use python-jose to convert JWK to PEM
                public_key_pem = jwk.construct(key).to_pem()
                return public_key_pem.decode("utf-8") if isinstance(public_key_pem, bytes) else public_key_pem
    
    raise ValueError(f"Key ID {kid} not found in JWKS")


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token from Supabase.
    
    - Validates signature using JWKS
    - Checks issuer and expiration
    - Returns verified claims
    
    Raises HTTPException if token is invalid.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    try:
        # Try to verify with JWKS first (production)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        public_key = get_public_key(token)
        
        # Verify token signature and claims
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.SUPABASE_KEY if settings.SUPABASE_KEY else None,
            issuer=f"{settings.SUPABASE_URL}/auth/v1" if settings.SUPABASE_URL else None,
        )
        return payload
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency to extract and verify the current user ID from JWT.
    
    Usage in routes:
        @router.get("/plants")
        def list_plants(user_id: str = Depends(get_current_user_id)):
            ...
    
    Raises HTTPException (401) if no valid token is provided.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Bearer token format: "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Only verify token if authentication is enabled
    if settings.REQUIRE_AUTH:
        payload = verify_jwt_token(token)
        user_id = payload.get("sub")  # Supabase uses 'sub' for user ID
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        return user_id
    else:
        # For development/testing without real Supabase, extract from test token
        # Test tokens can be: "Bearer test-user-id" or contain 'sub' in claims
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            if user_id:
                return user_id
        except:
            pass
        
        # Fallback to token itself as user_id for testing
        return token


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token without full verification.
    Used for test token creation and debugging.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")
    except:
        return None
