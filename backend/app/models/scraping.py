from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class ScraperType(str, Enum):
    BASIC = "basic"
    SELENIUM = "selenium"

class PaginationType(str, Enum):
    NEXT_BUTTON = "next_button"
    URL_PATTERN = "url_pattern"
    NONE = "none"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PaginationConfig(BaseModel):
    type: PaginationType
    pattern: Optional[str] = None  # For URL_PATTERN type
    selector: Optional[str] = None  # For NEXT_BUTTON type
    requires_javascript: bool = False

class ScrapingTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: HttpUrl
    selectors: Dict[str, str]
    scraper_type: ScraperType = ScraperType.BASIC
    pagination: Optional[PaginationConfig] = None
    max_pages: int = 1
    status: TaskStatus = TaskStatus.PENDING
    results: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
