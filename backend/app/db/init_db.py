import logging
import os
from pathlib import Path

from app.core.config import settings
from app.db.supabase import supabase_client

logger = logging.getLogger(__name__)

def init_db():
    """
    Initialize the database with required tables and RLS policies.
    This should be run when the application starts.
    """
    try:
        logger.info("Initializing database connection")
        
        # Test the connection
        response = supabase_client.table("users").select("count").limit(1).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Database connection error: {response.error}")
            raise Exception(f"Database connection error: {response.error}")
        
        logger.info("Database connection successful")
        
        # Create storage directories
        create_storage_directories()
        
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

def create_storage_directories():
    """
    Create all required storage directories.
    """
    try:
        logger.info("Creating storage directories")
        
        # Create main storage directory
        Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        directories = [
            settings.HTML_SNAPSHOTS_DIR,
            settings.SCREENSHOTS_DIR,
            settings.EXPORTS_DIR
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        logger.info("Storage directories created successfully")
    except Exception as e:
        logger.error(f"Error creating storage directories: {e}")
        raise

def create_admin_user(email: str, password: str):
    """
    Create an admin user if it doesn't exist.
    This should be run manually or during initial setup.
    
    Args:
        email: Admin user email
        password: Admin user password
    """
    try:
        # Check if user already exists
        response = supabase_client.table("users").select("*").eq("email", email).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error checking admin user: {response.error}")
            raise Exception(f"Error checking admin user: {response.error}")
        
        if response.data:
            logger.info(f"Admin user {email} already exists")
            
            # Update to ensure admin privileges
            update_response = supabase_client.table("users").update({"is_admin": True}).eq("email", email).execute()
            
            if hasattr(update_response, "error") and update_response.error is not None:
                logger.error(f"Error updating admin user: {update_response.error}")
            else:
                logger.info(f"Updated admin privileges for {email}")
                
            return
        
        # Create user in Supabase Auth
        auth_response = supabase_client.auth().sign_up({
            "email": email,
            "password": password
        })
        
        if hasattr(auth_response, "error") and auth_response.error is not None:
            logger.error(f"Error creating admin user in auth: {auth_response.error}")
            raise Exception(f"Error creating admin user in auth: {auth_response.error}")
        
        user_id = auth_response.user.id
        
        # Create user in our users table
        user_data = {
            "id": user_id,
            "email": email,
            "is_active": True,
            "is_admin": True
        }
        
        response = supabase_client.table("users").insert(user_data).execute()
        
        if hasattr(response, "error") and response.error is not None:
            logger.error(f"Error creating admin user in database: {response.error}")
            raise Exception(f"Error creating admin user in database: {response.error}")
        
        logger.info(f"Admin user {email} created successfully")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise
