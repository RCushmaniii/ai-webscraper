# AI WebScraper

> **Enterprise-grade web crawling and SEO analysis platform**

A full-stack web application for intelligent website crawling, SEO analysis, and content extraction. Built with React, FastAPI, and Supabase.

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/RCushmaniii/ai-webscraper)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

### 🎯 Core Functionality

- **Intelligent Web Crawling**: Advanced crawler with depth control, rate limiting, and robots.txt support
- **AI-Powered Content Analysis**: GPT-4 powered page summaries, categorization, and topic extraction
- **SEO Analysis**: Comprehensive SEO metadata extraction and AI-generated recommendations
- **Content Quality Scoring**: Automated content quality assessment with improvement suggestions
- **Image Accessibility**: AI-generated alt text for WCAG compliance
- **Link Analysis**: Internal/external link tracking and broken link detection
- **JavaScript Rendering**: Optional JS rendering for dynamic content

### 🎉 Production-Ready Extraction Features

- **✅ Link Extraction & Categorization**
  - Automatic internal/external link detection
  - Visual categorization with color-coded badges (Internal: Blue, External: Purple)
  - Interactive filter buttons with live counts
  - Broken link detection
- **✅ Image Extraction & Analysis**
  - Thumbnail previews for all extracted images
  - Alt text detection with missing indicators
  - Image dimensions display
  - Broken image detection
  - Source URL tracking
- **✅ SEO Metadata Extraction**
  - Complete metadata for every crawled page
  - Title, description, and meta tags
  - Structured data extraction
- **✅ Enhanced Detail Views**
  - **Links Tab**: Filter by All/Internal/External with real-time counts
  - **Images Tab**: Visual gallery with metadata and accessibility info
  - **Pages Tab**: Complete page list with status codes
  - **Issues Tab**: Ready for AI-generated issue detection

### 🔍 Search & Filtering (Phase 1)

- **✅ Global Search**

  - Full-text search across pages, links, and images
  - PostgreSQL GIN indexes for fast performance
  - Debounced search with grouped results
  - Image thumbnails in search results
  - Click to navigate to any result

- **✅ Advanced Sorting**
  - Sort pages by: Status Code, Title, Load Time, Date
  - Sort links by: Anchor Text, URL, Status Code
  - Sort images by: Alt Text Status, Broken Status, Size
  - Ascending/Descending toggle
  - Works with all existing filters

### 📊 Dashboard & Monitoring

- **World-Class Dashboard**: Real-time stats, recent crawls, and quick actions
- **Stale Crawl Monitoring**: Automatic detection and handling of stuck crawls
- **Activity Tracking**: Complete crawl history and status monitoring
- **Failed Crawl Alerts**: Instant notifications for failed operations

### 🔐 Security & Access Control

- **User Authentication**: Secure auth with Supabase
- **Row Level Security (RLS)**: Database-level access control
- **Admin Panel**: User management and system administration
- **Protected Routes**: Role-based access control

### 🎨 User Experience

- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Batch Operations**: Select and manage multiple crawls at once
- **Real-time Updates**: Live status updates during crawls
- **Export Functionality**: Download crawl data and reports

## 📋 Prerequisites

- **Node.js** (v16 or later)
- **Python** (3.9 or later)
- **npm** or **yarn**
- **Supabase** account (free tier available)
- **Git** for version control

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/RCushmaniii/ai-webscraper.git
cd ai-webscraper
```

### 2. Database Setup

1. Create a [Supabase](https://supabase.com) account and project
2. Run the migration scripts in order:
   - `database/migrations/PRODUCTION_READY_MIGRATION.sql`
   - `database/migrations/fix_status_constraint.sql`
   - `database/migrations/fix_all_rls_policies.sql`
3. Copy your Supabase URL and keys

### 3. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret_key
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_SUPABASE_URL=your_supabase_project_url
REACT_APP_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 5. Start Development Servers

**Option A: Use the startup script (Windows)**

```bash
start.bat
```

**Option B: Manual startup**

Terminal 1 (Backend):

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):

```bash
cd frontend
npm start
```

**Access the application:**

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 📁 Project Structure

```
ai-webscraper/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes and endpoints
│   │   │   └── routes/        # Route handlers
│   │   ├── core/              # Core configurations
│   │   ├── db/                # Database connections
│   │   ├── models/            # Pydantic models
│   │   └── services/          # Business logic
│   │       ├── crawler.py     # Web crawling engine
│   │       ├── crawl_monitor.py  # Stale crawl monitoring
│   │       └── worker.py      # Background task worker
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
├── frontend/                   # React frontend
│   ├── public/                # Static assets
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── contexts/          # React contexts (Auth, etc.)
│   │   ├── pages/             # Page components
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── CrawlsPage.tsx
│   │   │   ├── CrawlDetailPage.tsx
│   │   │   └── ...
│   │   ├── services/          # API service layer
│   │   └── lib/               # Utilities and helpers
│   ├── docs/                  # Design documentation
│   │   ├── BRAND.md           # Brand guidelines
│   │   └── DESIGN.md          # Design system
│   ├── package.json           # Node dependencies
│   └── .env                   # Environment variables
│
├── database/                   # Database files
│   ├── migrations/            # SQL migration scripts
│   └── README.md              # Database documentation
│
├── scripts/                    # Utility scripts
│   ├── query_constraint.py    # Database query tools
│   └── README.md              # Scripts documentation
│
├── docs/                       # Project documentation
│   └── images/                # Screenshots and diagrams
│
├── .windsurf/                  # IDE configuration
├── start.bat                   # Windows startup script
├── CHANGELOG.md                # Version history
└── README.md                   # This file
```

## ⚙️ Configuration

### Backend Environment Variables

| Variable                 | Description                       | Required |
| ------------------------ | --------------------------------- | -------- |
| `SUPABASE_URL`           | Your Supabase project URL         | ✅       |
| `SUPABASE_KEY`           | Supabase anon/public key          | ✅       |
| `OPENAI_API_KEY`         | OpenAI API key for LLM features   | ✅       |
| `OPENAI_PROJECT_ID`      | OpenAI project ID                 | ⚪       |
| `ENABLE_LLM_BASIC`       | Enable basic LLM analysis         | ⚪       |
| `ENABLE_LLM_ANALYSIS`    | Enable detailed LLM analysis      | ⚪       |
| `MAX_LLM_COST_PER_CRAWL` | Max LLM cost per crawl (USD)      | ⚪       |
| `BACKEND_CORS_ORIGINS`   | Allowed CORS origins (JSON array) | ✅       |

### Frontend Environment Variables

| Variable                      | Description          | Required |
| ----------------------------- | -------------------- | -------- |
| `REACT_APP_API_URL`           | Backend API URL      | ✅       |
| `REACT_APP_SUPABASE_URL`      | Supabase project URL | ✅       |
| `REACT_APP_SUPABASE_ANON_KEY` | Supabase anon key    | ✅       |

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Manual Testing

Use the provided test scripts:

```bash
python backend/test_crawl_direct.py
python backend/check_crawls.py
```

## 🚢 Deployment

See **[DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md)** for comprehensive deployment instructions.

### Quick Deployment Options

**Backend:**

- Railway (Recommended)
- Render
- Fly.io
- AWS/GCP/Azure

**Frontend:**

- Vercel (Recommended)
- Netlify
- AWS S3 + CloudFront

**Database:**

- Supabase (Managed PostgreSQL)

### Pre-Deployment Checklist

- [ ] Run database migrations
- [ ] Configure environment variables
- [ ] Test authentication flows
- [ ] Verify RLS policies
- [ ] Update CORS origins
- [ ] Test crawl functionality

## 🔧 Key Technologies

### Backend

- **FastAPI** - Modern Python web framework
- **OpenAI** - GPT-4 powered content analysis
- **Instructor** - Structured LLM outputs with Pydantic
- **Supabase Python Client** - Database and auth
- **BeautifulSoup4** - HTML parsing
- **Playwright** - JavaScript rendering
- **Pydantic** - Data validation

### Frontend

- **React** - UI library
- **React Router** - Navigation
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Supabase JS Client** - Auth and data
- **Sonner** - Toast notifications
- **Lucide React** - Icons

### Infrastructure

- **Supabase** - PostgreSQL database, auth, RLS
- **Background Tasks** - Automated monitoring

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[LLM_SERVICE.md](docs/LLM_SERVICE.md)** - AI-powered analysis features
- **[DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md)** - Deployment guide
- **[MIGRATION_INSTRUCTIONS.md](docs/MIGRATION_INSTRUCTIONS.md)** - Database migration guide
- **[database/README.md](database/README.md)** - Database documentation
- **[frontend/docs/BRAND.md](frontend/docs/BRAND.md)** - Brand guidelines
- **[frontend/docs/DESIGN.md](frontend/docs/DESIGN.md)** - Design system

## 📊 Success Metrics

All extraction features have been verified in production with real crawl data:

| Feature                   | Status     | Verified Count | Notes                             |
| ------------------------- | ---------- | -------------- | --------------------------------- |
| Pages Extraction          | ✅ Working | 1,150+         | Full page metadata and content    |
| Links Extraction          | ✅ Working | 292+           | Internal/External categorization  |
| Images Extraction         | ✅ Working | 187+           | With thumbnails and metadata      |
| SEO Metadata              | ✅ Working | 6+             | Complete meta tags per page       |
| Internal/External Filters | ✅ Working | Yes            | Real-time filtering in UI         |
| Image Thumbnails          | ✅ Working | Yes            | Visual previews with dimensions   |
| Alt Text Detection        | ✅ Working | Yes            | Accessibility compliance checking |
| Broken Link Detection     | ✅ Working | Yes            | Automatic validation              |

### Recent Production Test Results

**Test Crawl: https://www.smarttie.com.mx/**

- Pages Crawled: 5
- Links Extracted: 225 (Internal + External)
- Images Extracted: 187 (with full metadata)
- SEO Metadata: Complete for all pages
- Status: ✅ All features working perfectly

## 🎯 Key Features Explained

### Stale Crawl Monitoring

Automated background task that:

- Runs every 10 minutes
- Detects crawls stuck in running/queued/pending states
- Automatically marks stale crawls as failed
- Provides manual "Mark as Failed" button in UI
- Configurable timeouts (30min for running, 60min for queued)

### Dashboard Analytics

- **Stats Cards**: Total crawls, completed, active, pages crawled
- **Recent Activity**: Top 5 most recent crawls
- **Quick Actions**: One-click access to common tasks
- **Failed Crawl Alerts**: Instant visibility of issues

### Batch Operations

- Select multiple crawls with checkboxes
- Bulk delete operations
- Bulk re-run failed crawls
- Filter by status

### AI-Powered Analysis (LLM Service)

- **14 Analysis Tasks**: Page summaries, SEO recommendations, content quality scoring, and more
- **Cost Tracking**: Transparent LLM usage monitoring with budget controls
- **Tiered Analysis**: Basic ($0.0013/page), Detailed ($0.007/page), Full reports
- **Image Accessibility**: AI-generated alt text for WCAG compliance
- **Semantic Search**: Vector embeddings for finding similar content
- **Structured Outputs**: Reliable, parseable results with Pydantic validation

See **[LLM_SERVICE.md](docs/LLM_SERVICE.md)** for complete documentation.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

**Current Version: 1.1.0**

- ✅ **Phase 1: Search & Filtering** (NEW!)
  - Global full-text search across pages, links, and images
  - Advanced sorting on all tabs with ascending/descending toggle
  - PostgreSQL GIN indexes for optimized performance
  - Debounced search with grouped results dropdown
- ✅ **Production-Ready Extraction Features**
  - Link extraction with internal/external categorization (292+ links verified)
  - Image extraction with thumbnails and metadata (187+ images verified)
  - SEO metadata extraction (complete coverage)
  - Enhanced UI with filtering and visual galleries
- ✅ **RLS Authentication Fixed** - Service role client for reliable database writes
- ✅ **Database Schema Alignment** - Code matches exact schema
- ✅ **World-Class Dashboard** with real-time analytics
- ✅ **Automated Stale Crawl Monitoring**
- ✅ **Comprehensive Deployment Documentation**
- ✅ **Enterprise-Grade Security and Monitoring**

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI library
- [Supabase](https://supabase.io/) - Backend as a service
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [Lucide](https://lucide.dev/) - Beautiful icons

## 📧 Support

For issues, questions, or contributions:

- Open an issue on [GitHub](https://github.com/RCushmaniii/ai-webscraper/issues)
- Check the [documentation](docs/)
- Review the [deployment guide](docs/DEPLOYMENT_PLAN.md)

---

**Built with ❤️ by Robert Cushman**
