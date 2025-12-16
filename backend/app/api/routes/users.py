from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from app.core.auth import get_current_user, get_admin_user
from app.models.models import User, UserCreate, UserUpdate, UserResponse
from app.db.supabase import supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin
    }

@router.patch("/me/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile information.
    """
    try:
        # Prepare update data - only allow certain fields
        update_data = {}
        allowed_fields = ["full_name"]
        
        for field in allowed_fields:
            if field in profile_data:
                update_data[field] = profile_data[field]
        
        if not update_data:
            # Nothing to update
            return {
                "id": current_user.id,
                "email": current_user.email,
                "is_active": current_user.is_active,
                "is_admin": current_user.is_admin
            }
        
        # Update the user profile in Supabase
        response = supabase_client.table("users").update(update_data).eq("id", str(current_user.id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error updating user profile: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.post("/me/change-password", response_model=Dict[str, str])
async def change_user_password(
    password_data: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    """
    Change current user's password.
    """
    try:
        current_password = password_data.get("current_password")
        new_password = password_data.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(status_code=400, detail="Both current_password and new_password are required")
        
        # Use Supabase auth to update password
        # Note: This would typically require additional validation of current password
        # For now, we'll use Supabase's update user method
        
        try:
            # Update password via Supabase Auth API
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{supabase_client.auth_url}/user",
                    headers={
                        "apikey": supabase_client.supabase_key,
                        "Authorization": f"Bearer {current_user.id}"  # This would need the actual JWT token
                    },
                    json={
                        "password": new_password
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Supabase password update error: {response.status_code} - {response.text}")
                    raise HTTPException(status_code=500, detail="Failed to update password")
                
                return {"message": "Password updated successfully"}
                
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            raise HTTPException(status_code=500, detail="Failed to update password")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change password: {str(e)}")

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user)  # Only admins can list users
):
    """
    List all users (admin only).
    """
    try:
        response = supabase_client.table("users").select("*").range(skip, skip + limit - 1).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error listing users: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list users")
        
        # Add default values for missing fields
        users_data = []
        for user in response.data:
            user_dict = dict(user)
            # Set defaults for missing fields
            if 'is_active' not in user_dict:
                user_dict['is_active'] = True
            if 'full_name' not in user_dict:
                user_dict['full_name'] = None
            users_data.append(user_dict)
        
        return users_data
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user)  # Only admins can get other users
):
    """
    Get a specific user by ID (admin only).
    """
    try:
        response = supabase_client.table("users").select("*").eq("id", str(user_id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error getting user: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to get user")
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_admin_user)  # Only admins can update users
):
    """
    Update a user (admin only).
    """
    try:
        # First check if the user exists
        check_response = supabase_client.table("users").select("*").eq("id", str(user_id)).execute()
        
        if hasattr(check_response, "error") and check_response.error is not None:
            logger.error(f"Error checking user: {check_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check user")
        
        if not check_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {}
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        if user_update.is_admin is not None:
            update_data["is_admin"] = user_update.is_admin
        
        if not update_data:
            # Nothing to update
            return check_response.data[0]
        
        # Update the user
        response = supabase_client.table("users").update(update_data).eq("id", str(user_id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error updating user: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to update user")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user)  # Only admins can delete users
):
    """
    Delete a user (admin only).
    """
    try:
        # First check if the user exists
        check_response = supabase_client.table("users").select("*").eq("id", str(user_id)).execute()
        
        if hasattr(check_response, "error") and check_response.error is not None:
            logger.error(f"Error checking user: {check_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check user")
        
        if not check_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deleting yourself
        if str(user_id) == str(current_user.id):
            raise HTTPException(status_code=400, detail="Cannot delete your own user account")
        
        # Delete the user
        response = supabase_client.table("users").delete().eq("id", str(user_id)).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error deleting user: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to delete user")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.get("/{user_id}/audit-logs", response_model=List[Dict[str, Any]])
async def get_user_audit_logs(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user)  # Only admins can view audit logs
):
    """
    Get audit logs for a specific user (admin only).
    """
    try:
        response = supabase_client.table("audit_logs").select("*").eq("user_id", str(user_id)).range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error getting audit logs: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to get audit logs")
        
        return response.data
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@router.post("/invite", response_model=Dict[str, Any])
async def invite_user(
    user_create: UserCreate,
    current_user: User = Depends(get_admin_user)  # Only admins can invite users
):
    """
    Invite a new user (admin only).
    This endpoint doesn't actually create the user, but sends an invitation via Supabase.
    """
    try:
        # Check if user already exists
        check_response = supabase_client.table("users").select("*").eq("email", user_create.email).execute()
        
        if hasattr(check_response, "error") and check_response.error is not None:
            logger.error(f"Error checking user: {check_response.error}")
            raise HTTPException(status_code=500, detail="Failed to check user")
        
        if check_response.data:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Send invitation via Supabase Auth
        try:
            # Use httpx to make a request to Supabase auth API
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{supabase_client.auth_url}/invite",
                    headers={
                        "apikey": supabase_client.supabase_key,
                        "Authorization": f"Bearer {supabase_client.supabase_key}"
                    },
                    json={
                        "email": user_create.email,
                        "data": {
                            "is_admin": user_create.is_admin
                        }
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Supabase invite error: {response.status_code} - {response.text}")
                    raise HTTPException(status_code=500, detail="Failed to send invitation")
                
                return {"message": f"Invitation sent to {user_create.email}"}
                
        except Exception as e:
            logger.error(f"Error sending invitation: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send invitation: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invite user: {str(e)}")
