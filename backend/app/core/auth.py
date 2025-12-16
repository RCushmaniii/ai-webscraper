import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError

from app.core.config import settings
from app.models.models import User
from app.db.supabase import supabase_client

# Configure security
security = HTTPBearer()
logger = logging.getLogger(__name__)

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
        
        # Verify token with Supabase
        try:
            # Use httpx to make a request to Supabase auth API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.SUPABASE_URL}/auth/v1/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "apikey": settings.SUPABASE_KEY
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Supabase auth error: {response.status_code} - {response.text}")
                    raise credentials_exception
                
                user_data = response.json()
                
                # Check if user exists in our database
                db_user_response = supabase_client.table("users").select("*").eq("id", user_data["id"]).execute()
                
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
                    
                    create_response = supabase_client.table("users").insert(new_user).execute()
                    
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
