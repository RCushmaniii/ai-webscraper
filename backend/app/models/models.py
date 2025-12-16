from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl, validator


class UserBase(BaseModel):
    email: str
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserInDB(UserBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class User(UserBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class CrawlBase(BaseModel):
    url: str
    name: Optional[str] = None
    max_depth: int = 2
    max_pages: int = 100
    respect_robots_txt: bool = True
    follow_external_links: bool = False
    js_rendering: bool = False
    rate_limit: int = 2
    user_agent: Optional[str] = None
    max_runtime_sec: int = 3600
    internal_depth: int = 2
    follow_external: bool = False
    external_depth: int = 1


class CrawlCreate(CrawlBase):
    pass


class CrawlUpdate(BaseModel):
    url: Optional[str] = None
    internal_depth: Optional[int] = None
    follow_external: Optional[bool] = None
    external_depth: Optional[int] = None
    max_pages: Optional[int] = None
    max_runtime_sec: Optional[int] = None
    concurrency: Optional[int] = None
    rate_limit_rps: Optional[float] = None
    robots_policy: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CrawlInDB(CrawlBase):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    batch_id: Optional[UUID] = None
    status: str = "pending"
    error: Optional[str] = None
    pages_crawled: int = 0
    total_links: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Crawl(CrawlInDB):
    pass


class CrawlResponse(CrawlBase):
    id: UUID
    user_id: UUID
    status: str = "pending"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_pages: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageBase(BaseModel):
    url: str
    final_url: str
    status_code: Optional[int] = None
    method: str = "html"
    render_ms: Optional[int] = None
    content_hash: Optional[str] = None
    html_storage_path: Optional[str] = None
    text_excerpt: Optional[str] = None
    word_count: Optional[int] = None
    canonical_url: Optional[str] = None
    is_indexable: bool = True
    content_type: Optional[str] = None
    page_size_bytes: Optional[int] = None


class PageCreate(PageBase):
    crawl_id: UUID


class PageUpdate(BaseModel):
    final_url: Optional[str] = None
    status_code: Optional[int] = None
    method: Optional[str] = None
    render_ms: Optional[int] = None
    content_hash: Optional[str] = None
    html_storage_path: Optional[str] = None
    text_excerpt: Optional[str] = None
    word_count: Optional[int] = None
    canonical_url: Optional[str] = None
    is_indexable: Optional[bool] = None
    content_type: Optional[str] = None
    page_size_bytes: Optional[int] = None


class PageInDB(PageBase):
    id: UUID = Field(default_factory=uuid4)
    crawl_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class Page(PageInDB):
    pass


class SEOMetadataBase(BaseModel):
    title: Optional[str] = None
    title_length: Optional[int] = None
    meta_description: Optional[str] = None
    meta_description_length: Optional[int] = None
    h1: Optional[str] = None
    h2: Optional[List[str]] = None
    robots_meta: Optional[str] = None
    hreflang: Optional[Dict[str, Any]] = None
    canonical: Optional[str] = None
    og_tags: Optional[Dict[str, Any]] = None
    twitter_tags: Optional[Dict[str, Any]] = None
    json_ld: Optional[Dict[str, Any]] = None
    image_alt_missing_count: int = 0
    internal_links: int = 0
    external_links: int = 0


class SEOMetadataCreate(SEOMetadataBase):
    page_id: UUID


class SEOMetadataUpdate(SEOMetadataBase):
    pass


class SEOMetadataInDB(SEOMetadataBase):
    id: UUID = Field(default_factory=uuid4)
    page_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class SEOMetadata(SEOMetadataInDB):
    pass


class LinkBase(BaseModel):
    url: str
    anchor_text: Optional[str] = None
    link_type: str
    is_broken: bool = False
    status_code: Optional[int] = None
    error_message: Optional[str] = None


class LinkCreate(LinkBase):
    crawl_id: UUID
    source_page_id: UUID


class LinkUpdate(BaseModel):
    status_code: Optional[int] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None


class LinkInDB(LinkBase):
    id: UUID = Field(default_factory=uuid4)
    crawl_id: UUID
    source_page_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class Link(LinkInDB):
    pass


class IssueBase(BaseModel):
    type: str
    severity: str
    message: str
    pointer: Optional[str] = None
    context: Optional[str] = None


class IssueCreate(IssueBase):
    crawl_id: UUID
    page_id: Optional[UUID] = None


class IssueUpdate(IssueBase):
    pass


class IssueInDB(IssueBase):
    id: UUID = Field(default_factory=uuid4)
    crawl_id: UUID
    page_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class Issue(IssueInDB):
    pass


class SummaryBase(BaseModel):
    summary: str
    business_value: List[str]


class SummaryCreate(SummaryBase):
    page_id: Optional[UUID] = None
    crawl_id: UUID


class SummaryUpdate(SummaryBase):
    pass


class SummaryInDB(SummaryBase):
    id: UUID = Field(default_factory=uuid4)
    page_id: Optional[UUID] = None
    crawl_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Summary(SummaryInDB):
    pass


class BatchBase(BaseModel):
    name: str
    description: Optional[str] = None


class BatchCreate(BatchBase):
    urls: List[str]


class BatchUpdate(BatchBase):
    status: Optional[str] = None


class BatchInDB(BatchBase):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    status: str = "pending"
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Batch(BatchInDB):
    pass


class BatchResponse(BaseModel):
    id: UUID
    name: str
    notes: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_sites: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchSiteBase(BaseModel):
    url: str
    status: str = "pending"
    crawl_id: Optional[UUID] = None


class BatchSiteCreate(BatchSiteBase):
    batch_id: UUID


class BatchSiteUpdate(BaseModel):
    status: Optional[str] = None
    crawl_id: Optional[UUID] = None


class BatchSiteInDB(BatchSiteBase):
    id: UUID = Field(default_factory=uuid4)
    batch_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchSite(BatchSiteInDB):
    pass


class AuditLogCreate(BaseModel):
    user_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    details: Optional[Dict[str, Any]] = None


class AuditLogInDB(AuditLogCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLog(AuditLogInDB):
    pass


class GooglePlaceBase(BaseModel):
    place_id: str
    name: str
    address: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    reviews: Optional[Dict[str, Any]] = None


class GooglePlaceCreate(GooglePlaceBase):
    pass


class GooglePlaceUpdate(GooglePlaceBase):
    pass


class GooglePlaceInDB(GooglePlaceBase):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GooglePlace(GooglePlaceInDB):
    pass


class CrawlProgress(BaseModel):
    crawl_id: UUID
    status: str
    pages_crawled: int
    total_pages: int
    current_url: Optional[str] = None
    progress_percentage: float
    elapsed_time_seconds: int
    estimated_time_remaining_seconds: Optional[int] = None


class CrawlReport(BaseModel):
    crawl_id: UUID
    url: str
    total_pages: int
    status_code_distribution: Dict[str, int]
    avg_load_time_ms: float
    js_vs_html_ratio: float
    broken_links_count: int
    seo_issues_summary: Dict[str, int]
    content_overview: Dict[str, Any]
