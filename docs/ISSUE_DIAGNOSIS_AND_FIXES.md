# Critical Issues Diagnosis & Implementation Plan

**Date**: 2025-01-XX
**Status**: Production-Critical Bugs Identified
**Severity**: HIGH

---

## Issue 1: Images Tab Not Working

### **Diagnosis**

**ROOT CAUSE**: The Images tab does not exist in the frontend implementation.

**Evidence**:
- `CrawlDetailPage.tsx` only has 3 tabs: Pages, Links, Issues (lines 246-276)
- No Images tab UI component
- No state management for images data
- No API call to fetch images
- The crawler DOES extract image data (`crawler.py:426-427`)
- Database has no `images` table to store extracted image metadata

**Where the Problem Originates**:
1. **Frontend**: Missing tab implementation entirely
2. **Backend**: Images are counted but not stored as structured data
3. **Database**: No images table in schema

**Technical Details**:
- `PageDetailPage.tsx:208` shows `{page.images}` count from page data
- This `images` field doesn't exist in the actual database schema
- The crawler counts images (`image_alt_missing_count`) but doesn't save image URLs/metadata
- Only image-related data saved is `image_alt_missing_count` in seo_metadata table

### **Implementation Plan**

#### **Phase 1: Database Schema** (Required First)
```sql
-- Create images table
CREATE TABLE IF NOT EXISTS images (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  crawl_id UUID NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
  src TEXT NOT NULL,
  alt TEXT,
  title TEXT,
  width INT,
  height INT,
  file_size_bytes INT,
  has_alt BOOLEAN DEFAULT false,
  is_broken BOOLEAN DEFAULT false,
  status_code INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE images ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own images" ON images
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM crawls
      WHERE crawls.id = images.crawl_id
      AND crawls.user_id = auth.uid()
    )
  );

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_images_crawl_id ON images(crawl_id);
CREATE INDEX IF NOT EXISTS idx_images_page_id ON images(page_id);
CREATE INDEX IF NOT EXISTS idx_images_is_broken ON images(is_broken);
```

#### **Phase 2: Backend - Crawler Enhancement**
**File**: `backend/app/services/crawler.py`

Add new method to extract and save images:
```python
async def _extract_and_save_images(
    self,
    soup: BeautifulSoup,
    page_id: str,
    page_url: str
) -> None:
    """Extract images from page and save to database."""
    try:
        images = soup.find_all('img')

        for img in images:
            src = img.get('src')
            if not src:
                continue

            # Resolve relative URLs
            absolute_src = urljoin(page_url, src)

            image_data = {
                "id": str(uuid4()),
                "crawl_id": str(self.crawl.id),
                "page_id": str(page_id),
                "src": absolute_src,
                "alt": img.get('alt'),
                "title": img.get('title'),
                "width": img.get('width'),
                "height": img.get('height'),
                "has_alt": bool(img.get('alt')),
                "is_broken": False,  # Will check later
                "status_code": None,
                "file_size_bytes": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Save to database
            await self._save_image(image_data)

    except Exception as e:
        logger.error(f"Error extracting images: {e}")

async def _save_image(self, image_data: Dict) -> None:
    """Save image to database."""
    try:
        result = supabase_client.table("images").insert(image_data).execute()
        if hasattr(result, "error") and result.error:
            logger.error(f"Error saving image: {result.error}")
        else:
            logger.debug(f"Saved image {image_data['src'][:100]}")
    except Exception as e:
        logger.error(f"Error saving image: {e}")
```

Call this method in `_crawl_page` after line 262:
```python
# Extract links
if status_code == 200:
    await self._extract_and_process_links(soup, url, depth, page.id)
    # ADD THIS:
    await self._extract_and_save_images(soup, page.id, url)
```

#### **Phase 3: Backend - API Endpoint**
**File**: `backend/app/api/routes/crawls.py`

Add endpoint after line 372:
```python
@router.get("/{crawl_id}/images", response_model=List[Dict[str, Any]])
async def list_crawl_images(
    crawl_id: UUID,
    skip: int = 0,
    limit: int = 100,
    is_broken: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all images for a specific crawl with optional filters.
    """
    try:
        # Check crawl exists and belongs to user
        crawl_response = supabase_client.table("crawls").select("*").eq("id", str(crawl_id)).eq("user_id", str(current_user.id)).execute()

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        # Build query
        query = supabase_client.table("images").select("*").eq("crawl_id", str(crawl_id))

        if is_broken is not None:
            query = query.eq("is_broken", is_broken)

        response = query.range(skip, skip + limit - 1).execute()

        if hasattr(response, "error") and response.error:
            logger.error(f"Error listing images: {response.error}")
            raise HTTPException(status_code=500, detail="Failed to list images")

        return response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list images: {str(e)}")
```

#### **Phase 4: Frontend - API Service**
**File**: `frontend/src/services/api.ts`

Add interface and method:
```typescript
export interface Image {
  id: string;
  crawl_id: string;
  page_id: string;
  src: string;
  alt: string | null;
  title: string | null;
  width: number | null;
  height: number | null;
  has_alt: boolean;
  is_broken: boolean;
  status_code: number | null;
  file_size_bytes: number | null;
  created_at: string;
}

// Add to ApiService class:
async getCrawlImages(id: string, params?: {
  skip?: number;
  limit?: number;
  is_broken?: boolean;
}): Promise<Image[]> {
  const response = await this.api.get(`/crawls/${id}/images`, { params });
  return response.data;
}
```

#### **Phase 5: Frontend - Images Tab**
**File**: `frontend/src/pages/CrawlDetailPage.tsx`

1. Add state (after line 14):
```typescript
const [images, setImages] = useState<Image[]>([]);
```

2. Add tab button (after line 275):
```typescript
<button
  onClick={() => handleTabChange('images')}
  className={`py-4 text-sm font-medium border-b-2 ${
    activeTab === 'images'
      ? 'border-secondary-500 text-secondary-500'
      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
  }`}
>
  Images
</button>
```

3. Add to fetchTabData switch (after line 87):
```typescript
case 'images':
  if (images.length === 0) {
    const imagesData = await apiService.getCrawlImages(id);
    setImages(imagesData);
  }
  break;
```

4. Add Images tab content (after line 442):
```typescript
{/* Images Tab */}
{activeTab === 'images' && (
  <div className="p-6">
    <h2 className="mb-4 text-xl font-semibold text-gray-800">Images</h2>

    {images.length > 0 ? (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {images.map((image) => (
          <div
            key={image.id}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="aspect-video bg-gray-100 rounded-md mb-3 overflow-hidden flex items-center justify-center">
              <img
                src={image.src}
                alt={image.alt || 'No alt text'}
                className="max-w-full max-h-full object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.parentElement!.innerHTML = '<div class="text-gray-400 text-sm">Failed to load</div>';
                }}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {image.has_alt ? (
                  <span className="inline-flex px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                    Has Alt
                  </span>
                ) : (
                  <span className="inline-flex px-2 py-1 text-xs font-semibold text-orange-800 bg-orange-100 rounded-full">
                    Missing Alt
                  </span>
                )}

                {image.is_broken && (
                  <span className="inline-flex px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                    Broken
                  </span>
                )}
              </div>

              {image.alt && (
                <p className="text-sm text-gray-700 line-clamp-2" title={image.alt}>
                  <strong>Alt:</strong> {image.alt}
                </p>
              )}

              <p className="text-xs text-gray-500 truncate" title={image.src}>
                {image.src}
              </p>

              {(image.width && image.height) && (
                <p className="text-xs text-gray-500">
                  {image.width} × {image.height}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
        <p>No images found for this crawl.</p>
      </div>
    )}
  </div>
)}
```

### **Testing Checklist**
- [ ] Database migration applied successfully
- [ ] Crawler extracts and saves images
- [ ] API endpoint returns images list
- [ ] Images tab displays in UI
- [ ] Images render correctly
- [ ] Alt text status displays correctly
- [ ] Broken images show error state
- [ ] Empty state shows when no images
- [ ] Pagination works (if many images)

---

## Issue 2: Page Content Truncated

### **Diagnosis**

**ROOT CAUSE**: Hardcoded 1000-character limit in crawler

**Evidence**:
- `crawler.py:235` - `text_excerpt = extracted_data['content']['text'][:1000]`
- Database schema uses `TEXT` type (unlimited) - so DB is fine
- API returns raw `page.text_excerpt` field which is truncated
- Frontend displays this truncated content

**Where the Problem Originates**:
1. **Crawler**: Line 235 applies `:1000` slice
2. **Database**: Field type is fine (TEXT can hold unlimited)
3. **API**: Just passes through truncated data
4. **Frontend**: Displays what API returns

**Why This is Critical**:
- User cannot see full page content
- Defeats purpose of web scraping
- Data loss on every crawl
- No way to recover full content later

### **Implementation Plan**

#### **Option A: Store Full Content (Recommended)**

**Database Migration**:
```sql
-- Add new column for full content
ALTER TABLE pages ADD COLUMN full_content TEXT;

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_pages_full_content_fts
ON pages USING gin(to_tsvector('english', full_content));
```

**Crawler Change** (`crawler.py:235-248`):
```python
# Extract full text content
full_content = extracted_data['content']['text'] if extracted_data['content']['text'] else self._extract_text_excerpt(soup)
text_excerpt = full_content[:1000]  # Keep excerpt for listings

# Create page record
page = Page(
    crawl_id=self.crawl.id,
    url=url,
    final_url=final_url,
    status_code=status_code,
    method=method,
    render_ms=render_time,
    content_hash=content_hash,
    html_storage_path=html_storage_path,
    text_excerpt=text_excerpt,
    full_content=full_content,  # ADD THIS
    word_count=word_count,
    content_type=content_type,
    page_size_bytes=len(html_content)
)
```

**API Enhancement** (`crawls.py:320`):
```python
# Get the specific page with full content
response = supabase_client.table("pages")\
    .select("*")\
    .eq("id", str(page_id))\
    .eq("crawl_id", str(crawl_id))\
    .single()\
    .execute()

if not response.data:
    raise HTTPException(status_code=404, detail="Page not found")

page_data = response.data

# Return full content for detail view
return {
    "id": page_data["id"],
    "crawl_id": page_data["crawl_id"],
    "url": page_data["url"],
    "title": page_data.get("text_excerpt", "")[:100],  # Title from excerpt
    "meta_description": None,  # Get from seo_metadata if needed
    "content_summary": page_data.get("full_content") or page_data.get("text_excerpt", ""),  # FULL CONTENT HERE
    "status_code": page_data["status_code"],
    "response_time": page_data.get("render_ms", 0),
    "content_type": page_data.get("content_type", ""),
    "content_length": page_data.get("page_size_bytes", 0),
    "h1_tags": [],  # Get from seo_metadata
    "h2_tags": [],  # Get from seo_metadata
    "internal_links": 0,  # Get from seo_metadata
    "external_links": 0,  # Get from seo_metadata
    "images": 0,  # Get from images table count
    "created_at": page_data["created_at"]
}
```

**Frontend Update** (`PageDetailPage.tsx`):
No changes needed - already displays `content_summary`

#### **Option B: Load from HTML Storage (Alternative)**

If full_content storage is too large, load from stored HTML file:

```python
@router.get("/{crawl_id}/pages/{page_id}/full-content")
async def get_page_full_content(
    crawl_id: UUID,
    page_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get full page content from stored HTML."""
    # ... auth checks ...

    page = response.data
    html_path = page.get("html_storage_path")

    if not html_path:
        raise HTTPException(status_code=404, detail="HTML not stored")

    # Read HTML file
    html_content = await read_html_snapshot(html_path)

    # Extract text
    extractor = SmartContentExtractor(html_content, page["url"])
    extracted = extractor.extract_all_data()

    return {
        "full_content": extracted['content']['text']
    }
```

### **Recommendation**
Use **Option A** - store full_content in database for:
- Faster access
- No file I/O overhead
- Better for search/analysis
- Disk is cheap, user experience is not

### **Testing Checklist**
- [ ] Database migration applied
- [ ] New crawls save full_content
- [ ] Page detail API returns full content
- [ ] Frontend displays complete content (not truncated)
- [ ] Long content renders without breaking UI
- [ ] Copy to clipboard works with full content

---

## Issue 3: Admin Editing & Crawl Configuration

### **Diagnosis**

**ROOT CAUSE**: No edit functionality implemented

**Evidence**:
- No UPDATE endpoint for crawls in API
- No edit modal/form in frontend
- Re-run creates new crawl instead of modifying existing
- Cannot change crawl name after creation
- Cannot adjust parameters before re-running

**Where the Problem Originates**:
1. **API**: Missing `PATCH /crawls/{id}` endpoint
2. **Frontend**: No edit UI component
3. **Business Logic**: Re-run is "create new" not "edit and retry"

### **Implementation Plan**

#### **Phase 1: Backend - Update Endpoint**
**File**: `backend/app/api/routes/crawls.py`

```python
from pydantic import BaseModel

class CrawlUpdate(BaseModel):
    """Model for updating crawl configuration"""
    name: Optional[str] = None
    url: Optional[str] = None
    max_depth: Optional[int] = None
    max_pages: Optional[int] = None
    respect_robots_txt: Optional[bool] = None
    follow_external_links: Optional[bool] = None
    js_rendering: Optional[bool] = None
    rate_limit: Optional[float] = None
    user_agent: Optional[str] = None

@router.patch("/{crawl_id}", response_model=Dict[str, Any])
async def update_crawl(
    crawl_id: UUID,
    crawl_update: CrawlUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update crawl configuration.
    Only allowed for pending/failed crawls.
    """
    try:
        # Check crawl exists and belongs to user
        crawl_response = supabase_client.table("crawls")\
            .select("*")\
            .eq("id", str(crawl_id))\
            .eq("user_id", str(current_user.id))\
            .single()\
            .execute()

        if not crawl_response.data:
            raise HTTPException(status_code=404, detail="Crawl not found")

        crawl = crawl_response.data

        # Only allow editing pending/failed/completed crawls
        if crawl["status"] in ["running", "in_progress"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot edit running crawl"
            )

        # Build update dict (only include provided fields)
        update_data = {
            "updated_at": datetime.now().isoformat()
        }

        if crawl_update.name is not None:
            update_data["name"] = crawl_update.name
        if crawl_update.url is not None:
            update_data["url"] = crawl_update.url
        if crawl_update.max_depth is not None:
            update_data["max_depth"] = crawl_update.max_depth
        if crawl_update.max_pages is not None:
            update_data["max_pages"] = crawl_update.max_pages
        if crawl_update.respect_robots_txt is not None:
            update_data["respect_robots_txt"] = crawl_update.respect_robots_txt
        if crawl_update.follow_external_links is not None:
            update_data["follow_external_links"] = crawl_update.follow_external_links
        if crawl_update.js_rendering is not None:
            update_data["js_rendering"] = crawl_update.js_rendering
        if crawl_update.rate_limit is not None:
            update_data["rate_limit"] = crawl_update.rate_limit
        if crawl_update.user_agent is not None:
            update_data["user_agent"] = crawl_update.user_agent

        # Update in database
        response = supabase_client.table("crawls")\
            .update(update_data)\
            .eq("id", str(crawl_id))\
            .execute()

        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=500, detail="Failed to update crawl")

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating crawl: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update: {str(e)}")
```

#### **Phase 2: Frontend - API Service**
**File**: `frontend/src/services/api.ts`

```typescript
export interface CrawlUpdate {
  name?: string;
  url?: string;
  max_depth?: number;
  max_pages?: number;
  respect_robots_txt?: boolean;
  follow_external_links?: boolean;
  js_rendering?: boolean;
  rate_limit?: number;
  user_agent?: string;
}

// Add to ApiService class:
async updateCrawl(id: string, updates: CrawlUpdate): Promise<Crawl> {
  const response = await this.api.patch(`/crawls/${id}`, updates);
  return response.data;
}
```

#### **Phase 3: Frontend - Edit Modal**
**File**: `frontend/src/components/EditCrawlModal.tsx` (NEW FILE)

```typescript
import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Crawl, CrawlUpdate } from '../services/api';

interface EditCrawlModalProps {
  crawl: Crawl;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updates: CrawlUpdate) => Promise<void>;
}

const EditCrawlModal: React.FC<EditCrawlModalProps> = ({
  crawl,
  isOpen,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = useState<CrawlUpdate>({
    name: crawl.name,
    url: crawl.url,
    max_depth: crawl.max_depth,
    max_pages: crawl.max_pages,
    respect_robots_txt: crawl.respect_robots_txt,
    follow_external_links: crawl.follow_external_links,
    js_rendering: crawl.js_rendering,
    rate_limit: crawl.rate_limit,
    user_agent: crawl.user_agent
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(formData);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Edit Crawl Settings</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Crawl Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500"
              />
            </div>

            {/* URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start URL
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Max Depth */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Depth
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.max_depth}
                  onChange={(e) => setFormData({ ...formData, max_depth: Number(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500"
                />
              </div>

              {/* Max Pages */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Pages
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={formData.max_pages}
                  onChange={(e) => setFormData({ ...formData, max_pages: Number(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500"
                />
              </div>
            </div>

            {/* Checkboxes */}
            <div className="space-y-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.respect_robots_txt}
                  onChange={(e) => setFormData({ ...formData, respect_robots_txt: e.target.checked })}
                  className="w-4 h-4 text-secondary-500 border-gray-300 rounded focus:ring-secondary-500"
                />
                <span className="text-sm text-gray-700">Respect robots.txt</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.follow_external_links}
                  onChange={(e) => setFormData({ ...formData, follow_external_links: e.target.checked })}
                  className="w-4 h-4 text-secondary-500 border-gray-300 rounded focus:ring-secondary-500"
                />
                <span className="text-sm text-gray-700">Follow external links</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.js_rendering}
                  onChange={(e) => setFormData({ ...formData, js_rendering: e.target.checked })}
                  className="w-4 h-4 text-secondary-500 border-gray-300 rounded focus:ring-secondary-500"
                />
                <span className="text-sm text-gray-700">Enable JavaScript rendering</span>
              </label>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-white bg-secondary-600 rounded-lg hover:bg-secondary-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditCrawlModal;
```

#### **Phase 4: Integrate into CrawlDetailPage**
**File**: `frontend/src/pages/CrawlDetailPage.tsx`

Add state and handlers:
```typescript
import EditCrawlModal from '../components/EditCrawlModal';

// Add state
const [showEditModal, setShowEditModal] = useState(false);

// Add handler
const handleEditCrawl = async (updates: CrawlUpdate) => {
  if (!id) return;

  try {
    await apiService.updateCrawl(id, updates);
    toast.success('Crawl updated successfully');
    fetchCrawl(); // Refresh crawl data
  } catch (err) {
    console.error('Error updating crawl:', err);
    toast.error('Failed to update crawl');
  }
};

// Add Edit button in header (after status badge, before Re-run)
<button
  onClick={() => setShowEditModal(true)}
  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500"
>
  Edit Settings
</button>

// Add modal at bottom
<EditCrawlModal
  crawl={crawl}
  isOpen={showEditModal}
  onClose={() => setShowEditModal(false)}
  onSave={handleEditCrawl}
/>
```

### **Testing Checklist**
- [ ] Edit button appears on crawl detail page
- [ ] Modal opens with current settings
- [ ] Form validates inputs
- [ ] API updates crawl settings
- [ ] Cannot edit running crawls
- [ ] Changes reflect immediately
- [ ] Re-run uses updated settings

---

## Issue 4: Rerun Title Appending

### **Diagnosis**

**ROOT CAUSE**: Naive string concatenation

**Evidence**:
- `CrawlDetailPage.tsx:129` - `name: \`${crawl.name} (Re-run)\``
- No check if "(Re-run)" already exists
- Creates: "My Crawl (Re-run) (Re-run) (Re-run)"

**Better Approaches**:
1. Don't append anything (keep original name)
2. Add timestamp: "My Crawl - 2025-01-15 14:30"
3. Add counter: "My Crawl #2"
4. Let user rename during re-run

### **Implementation Plan**

#### **Option A: Keep Original Name (Simplest)**
```typescript
const handleRerun = async () => {
  if (!crawl) return;

  setShowRerunConfirm(false);
  setRerunning(true);

  try {
    await apiService.createCrawl({
      url: crawl.url,
      name: crawl.name,  // JUST USE ORIGINAL NAME
      max_depth: crawl.max_depth,
      // ... rest
    });
    toast.success('Crawl re-run initiated successfully');
    navigate('/crawls');
  } catch (err) {
    // ...
  }
};
```

#### **Option B: Add Timestamp (Recommended)**
```typescript
const handleRerun = async () => {
  if (!crawl) return;

  setShowRerunConfirm(false);
  setRerunning(true);

  // Remove any existing timestamp or "(Re-run)" suffix
  let baseName = crawl.name
    .replace(/\s*\(Re-run\)\s*/g, '')  // Remove "(Re-run)"
    .replace(/\s*-\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}.*$/, '');  // Remove timestamp

  // Add current timestamp
  const timestamp = new Date().toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  const newName = `${baseName} - ${timestamp}`;

  try {
    await apiService.createCrawl({
      url: crawl.url,
      name: newName,  // "My Crawl - Jan 15, 02:30 PM"
      max_depth: crawl.max_depth,
      // ... rest
    });
    toast.success('Crawl re-run initiated successfully');
    navigate('/crawls');
  } catch (err) {
    // ...
  }
};
```

#### **Option C: Smart Increment**
```typescript
const handleRerun = async () => {
  if (!crawl) return;

  setShowRerunConfirm(false);
  setRerunning(true);

  // Remove existing counter
  let baseName = crawl.name.replace(/\s*#\d+$/, '').replace(/\s*\(Re-run\)\s*/g, '');

  // Get all crawls to find next number
  const allCrawls = await apiService.getCrawls();
  const pattern = new RegExp(`^${baseName}(\\s*#(\\d+))?$`);
  const numbers = allCrawls
    .map(c => c.name.match(pattern)?.[2])
    .filter(Boolean)
    .map(Number);

  const nextNum = numbers.length > 0 ? Math.max(...numbers) + 1 : 2;
  const newName = `${baseName} #${nextNum}`;

  try {
    await apiService.createCrawl({
      url: crawl.url,
      name: newName,  // "My Crawl #2"
      max_depth: crawl.max_depth,
      // ... rest
    });
    // ...
  } catch (err) {
    // ...
  }
};
```

### **Recommendation**
Use **Option B (Timestamp)** because:
- User can see when each run happened
- No database queries needed
- Clear chronological order
- Example: "My Site Crawl - Jan 15, 2:30 PM"

### **Testing Checklist**
- [ ] First re-run creates clean name
- [ ] Second re-run doesn't duplicate suffix
- [ ] Timestamp format is readable
- [ ] Works with crawls that already have "(Re-run)" in name
- [ ] Preserves original base name

---

## Summary of Changes

### Database Migrations Required
1. **images table** - New table for image storage
2. **pages.full_content** - New column for complete content

### Backend Changes
1. **crawler.py** - Extract and save images, store full content
2. **crawls.py** - Add images endpoint, update endpoint, fix page detail
3. **models.py** - Add Image model, CrawlUpdate schema

### Frontend Changes
1. **api.ts** - Add getCrawlImages, updateCrawl methods
2. **CrawlDetailPage.tsx** - Add Images tab, Edit button, fix re-run naming
3. **EditCrawlModal.tsx** - New component for editing crawls
4. **PageDetailPage.tsx** - Display full content (no changes if using full_content field)

### Implementation Order
1. Apply database migrations
2. Update backend (crawler + API)
3. Update frontend API service
4. Update frontend UI components
5. Test each feature thoroughly

### Estimated Impact
- **Images Tab**: Medium effort, high user value
- **Content Fix**: Low effort, critical fix
- **Edit Feature**: Medium effort, high admin value
- **Rerun Naming**: Trivial effort, quality improvement

All issues are production-critical and should be addressed before next release.