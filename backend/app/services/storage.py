import os
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID
import aiofiles
import httpx
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure storage directories exist
def ensure_storage_dirs():
    """Ensure all required storage directories exist."""
    dirs = [
        settings.HTML_SNAPSHOTS_DIR,
        settings.SCREENSHOTS_DIR,
        settings.EXPORTS_DIR
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

# Initialize storage on startup
ensure_storage_dirs()

async def store_html_snapshot(crawl_id: UUID, url: str, html_content: str) -> str:
    """
    Store HTML snapshot in the file system.
    Returns the relative storage path.
    """
    # Create a safe filename from URL
    safe_url = "".join(c if c.isalnum() else "_" for c in url)
    safe_url = safe_url[:100]  # Limit length
    
    # Create directory for this crawl if it doesn't exist
    crawl_dir = Path(settings.HTML_SNAPSHOTS_DIR) / str(crawl_id)
    crawl_dir.mkdir(exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_url}_{timestamp}.html"
    file_path = crawl_dir / filename
    
    # Write HTML content to file
    try:
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(html_content)
        
        # Return relative path from storage root
        return str(file_path.relative_to(Path(settings.STORAGE_DIR)))
    
    except Exception as e:
        logger.error(f"Error storing HTML snapshot: {e}")
        return ""

async def store_screenshot(crawl_id: UUID, url: str, screenshot_bytes: bytes) -> str:
    """
    Store screenshot in the file system.
    Returns the relative storage path.
    """
    # Create a safe filename from URL
    safe_url = "".join(c if c.isalnum() else "_" for c in url)
    safe_url = safe_url[:100]  # Limit length
    
    # Create directory for this crawl if it doesn't exist
    crawl_dir = Path(settings.SCREENSHOTS_DIR) / str(crawl_id)
    crawl_dir.mkdir(exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_url}_{timestamp}.png"
    file_path = crawl_dir / filename
    
    # Write screenshot bytes to file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(screenshot_bytes)
        
        # Return relative path from storage root
        return str(file_path.relative_to(Path(settings.STORAGE_DIR)))
    
    except Exception as e:
        logger.error(f"Error storing screenshot: {e}")
        return ""

async def store_export(crawl_id: UUID, export_type: str, content: bytes) -> str:
    """
    Store export file (CSV, PDF, JSON) in the file system.
    Returns the relative storage path.
    """
    # Create directory for this crawl if it doesn't exist
    crawl_dir = Path(settings.EXPORTS_DIR) / str(crawl_id)
    crawl_dir.mkdir(exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{export_type}_{timestamp}.{export_type}"
    file_path = crawl_dir / filename
    
    # Write content to file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Return relative path from storage root
        return str(file_path.relative_to(Path(settings.STORAGE_DIR)))
    
    except Exception as e:
        logger.error(f"Error storing export: {e}")
        return ""

async def get_file_content(file_path: str) -> Optional[bytes]:
    """
    Get file content from storage.
    Returns None if file doesn't exist.
    """
    full_path = Path(settings.STORAGE_DIR) / file_path
    
    if not full_path.exists():
        return None
    
    try:
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()
    
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

async def delete_crawl_data(crawl_id: UUID) -> bool:
    """
    Delete all data associated with a crawl.
    Returns True if successful, False otherwise.
    """
    dirs = [
        Path(settings.HTML_SNAPSHOTS_DIR) / str(crawl_id),
        Path(settings.SCREENSHOTS_DIR) / str(crawl_id),
        Path(settings.EXPORTS_DIR) / str(crawl_id)
    ]
    
    success = True
    
    for dir_path in dirs:
        if dir_path.exists():
            try:
                for file_path in dir_path.glob('*'):
                    file_path.unlink()
                dir_path.rmdir()
            except Exception as e:
                logger.error(f"Error deleting crawl data: {e}")
                success = False
    
    return success
