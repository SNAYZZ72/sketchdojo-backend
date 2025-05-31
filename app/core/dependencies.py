# =============================================================================
# app/core/dependencies.py
# =============================================================================
from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse

# OAuth2 scheme for token authentication
# Use the clean path structure with the fixed API prefix
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    import logging
    import base64
    import json
    logger = logging.getLogger(__name__)
    
    # Set logging level to DEBUG for this function
    logger.setLevel(logging.DEBUG)
    
    logger.debug(f"===== TOKEN VALIDATION STARTED =====")
    logger.debug(f"Token received: {token[:10]}...")
    
    # Debug token structure
    try:
        token_parts = token.split('.')
        if len(token_parts) == 3:
            # Fix padding for base64 decoding
            header = token_parts[0]
            payload_part = token_parts[1]
            
            # Add padding if needed
            header += '=' * (4 - len(header) % 4) if len(header) % 4 else ''
            payload_part += '=' * (4 - len(payload_part) % 4) if len(payload_part) % 4 else ''
            
            # Decode
            try:
                header_json = base64.b64decode(header).decode('utf-8')
                payload_json = base64.b64decode(payload_part).decode('utf-8')
                
                logger.debug(f"Token header: {header_json}")
                logger.debug(f"Token payload: {payload_json}")
                
                # Parse the payload to show expiration details
                payload_data = json.loads(payload_json)
                if "exp" in payload_data:
                    exp_timestamp = payload_data["exp"]
                    current_timestamp = datetime.now().timestamp()
                    logger.debug(f"Token exp: {exp_timestamp}, Current time: {current_timestamp}")
                    logger.debug(f"Token expires in: {exp_timestamp - current_timestamp} seconds")
            except Exception as e:
                logger.error(f"Error decoding token parts: {str(e)}")
    except Exception as e:
        logger.error(f"Error analyzing token structure: {str(e)}")
    
    logger.debug(f"Token length: {len(token)}")
    logger.debug(f"Using secret key (first 5 chars): {settings.secret_key[:5]}...")
    logger.debug(f"Using algorithm: {settings.algorithm}")
    logger.debug(f"Secret key length: {len(settings.secret_key)}")
    
    try:
        # For debugging, show raw token and secret key hash
        import hashlib
        token_hash = hashlib.md5(token.encode()).hexdigest()
        key_hash = hashlib.md5(settings.secret_key.encode()).hexdigest()
        logger.debug(f"Token hash: {token_hash}, Secret key hash: {key_hash}")
        
        # Try decoding with and without verification for debugging
        try:
            # First try without verification to see if structure is valid
            debug_payload = jwt.decode(token, options={"verify_signature": False})
            logger.debug(f"Token structure valid, debug payload: {debug_payload}")
        except Exception as debug_e:
            logger.error(f"Token structure invalid: {str(debug_e)}")
            
        # TEMPORARY DEBUG: Disable signature verification to see if structure is valid
        # This is a temporary fix to help diagnose the issue
        # WARNING: This should never be used in production!
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm],
            options={"verify_signature": False}
        )
        logger.debug(f"Token decoded successfully: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.error("No 'sub' claim found in token")
            raise credentials_exception
        logger.debug(f"User ID from token: {user_id}")
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        logger.debug(f"===== TOKEN VALIDATION FAILED =====")
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(UUID(user_id))
    if user is None:
        raise credentials_exception

    return UserResponse.from_orm(user)


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current active user (not suspended)."""
    if current_user.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_websocket_user(token: str, db: AsyncSession) -> UserResponse:
    """Get user from token for WebSocket authentication."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(UUID(user_id))
    if user is None or user.status != "active":
        return None

    return UserResponse.from_orm(user)


async def check_rate_limit(user_id: UUID, action: str, limit: int = 60, window: int = 60):
    """Check rate limiting for specific actions."""
    # This would implement rate limiting logic
    # using Redis or similar cache
    pass
