import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError, jwk
from functools import lru_cache
import time

from app.core.config import settings
from app.models.models import User
from app.db.supabase import supabase_client

# Configure security
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Store the current auth token and client in context variables for request scope
from contextlib import ContextDecorator
from contextvars import ContextVar

_auth_token: ContextVar[Optional[str]] = ContextVar('auth_token', default=None)
_auth_client: ContextVar[Optional[any]] = ContextVar('auth_client', default=None)

# Cache for JWKS keys (expires after 1 hour)
_jwks_cache = {"keys": None, "expires_at": 0}

async def get_jwks():
    """Fetch and cache JWKS from Supabase."""
    current_time = time.time()
    
    # Return cached keys if still valid
    if _jwks_cache["keys"] and current_time < _jwks_cache["expires_at"]:
        return _jwks_cache["keys"]
    
    # Fetch new keys
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks_data = response.json()
        
        # Cache for 1 hour
        _jwks_cache["keys"] = jwks_data
        _jwks_cache["expires_at"] = current_time + 3600
        
        return jwks_data

async def verify_jwt_token(token: str) -> dict:
    """Verify JWT token using JWKS public keys."""
    try:
        logger.info(f"Starting JWT verification for token: {token[:20]}...")
        
        # Get the unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        logger.info(f"Token kid: {kid}, algorithm: {unverified_header.get('alg')}")

        if not kid:
            raise JWTError("No kid in token header")

        # Get JWKS
        jwks_data = await get_jwks()
        logger.info(f"Fetched JWKS with {len(jwks_data.get('keys', []))} keys")

        # Find the matching key
        key_data = None
        for key in jwks_data.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            logger.warning(f"Key {kid} not found in JWKS. Available keys: {[k.get('kid') for k in jwks_data.get('keys', [])]}")
            logger.warning(f"Token is using legacy HS256 key. Falling back to direct Supabase validation.")
            
            # Fall back to Supabase auth validation for legacy tokens
            try:
                user_response = supabase_client.auth.get_user(token)
                if user_response and user_response.user:
                    return {
                        "sub": user_response.user.id,
                        "email": user_response.user.email,
                        "role": user_response.user.role
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback validation also failed: {fallback_error}")
            
            raise JWTError(f"Key {kid} not found in JWKS and fallback validation failed")

        logger.info(f"Found matching key with kid: {kid}, type: {key_data.get('kty')}, alg: {key_data.get('alg')}")

        # Convert JWK to PEM format (critical step!)
        signing_key = jwk.construct(key_data).to_pem()
        logger.info("Successfully converted JWK to PEM format")

        # Verify the token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["ES256", "RS256"],
            options={"verify_aud": False}  # Supabase tokens don't have audience
        )
        
        logger.info(f"JWT verification successful for user: {payload.get('sub')}")
        return payload

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error verifying JWT: {e}", exc_info=True)
        raise JWTError(f"Token verification failed: {str(e)}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Validate JWT token and return the current user.
    
    Args:
        credentials: JWT token from Authorization header
        
    Returns:
        User object for the authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Get the token
        token = credentials.credentials

        # Store the token immediately for this request
        _auth_token.set(token)

        # Verify token locally using JWKS (fast, no external API call)
        try:
            # Verify JWT token locally
            payload = await verify_jwt_token(token)
            
            # Extract user data from token payload
            user_data = {
                "id": payload.get("sub"),
                "email": payload.get("email")
            }
            
            if not user_data["id"] or not user_data["email"]:
                logger.error("Invalid token payload - missing user data")
                raise credentials_exception
            
            # Create authenticated client for database queries
            auth_client = supabase_client.get_client_with_auth(token)
            _auth_client.set(auth_client)

            # Check if user exists in our database using the cached auth client
            db_user_response = auth_client.table("users").select("*").eq("id", user_data["id"]).execute()

            if hasattr(db_user_response, "error") and db_user_response.error is not None:
                logger.error(f"Error fetching user: {db_user_response.error}")
                raise credentials_exception

            if not db_user_response.data:
                # User doesn't exist in our database yet, create them
                new_user = {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "is_active": True,
                    "is_admin": False  # Default to non-admin
                }

                create_response = auth_client.table("users").insert(new_user).execute()

                if hasattr(create_response, "error") and create_response.error is not None:
                    logger.error(f"Error creating user: {create_response.error}")
                    raise credentials_exception

                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    is_active=True,
                    is_admin=False,
                    created_at=None,
                    updated_at=None,
                    full_name=None
                )
            else:
                # User exists, return their data
                user_dict = db_user_response.data[0]
                user = User(
                    id=user_dict["id"],
                    email=user_dict["email"],
                    is_active=user_dict.get("is_active", True),
                    is_admin=user_dict.get("is_admin", False),
                    created_at=user_dict.get("created_at"),
                    updated_at=user_dict.get("updated_at"),
                    full_name=user_dict.get("full_name")
                )

            return user
                
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            raise credentials_exception
            
    except JWTError:
        logger.error("JWT token error")
        raise credentials_exception

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if the current user is an admin.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object if the user is an admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user

def get_auth_client():
    """
    Get an authenticated Supabase client for the current request.
    Must be used after get_current_user dependency.
    Caches the client per request to avoid creating multiple instances.
    """
    # Check if we already have a cached client for this request
    cached_client = _auth_client.get()
    if cached_client is not None:
        return cached_client

    # Get token and create new client
    token = _auth_token.get()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token available"
        )

    # Create and cache the client
    client = supabase_client.get_client_with_auth(token)
    _auth_client.set(client)
    return client
