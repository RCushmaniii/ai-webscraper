import React, { useState } from 'react';
import { Book, Code, Settings, Shield, BarChart3, Layers, ChevronRight, ChevronDown } from 'lucide-react';
import Footer from '../components/Footer';

interface DocSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: DocItem[];
}

interface DocItem {
  id: string;
  title: string;
  content: string;
}

const DocsPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('overview');  // Auto-load Platform Overview
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['introduction']));

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const docSections: DocSection[] = [
    {
      id: 'introduction',
      title: 'Introduction',
      icon: <Book className="h-4 w-4" />,
      items: [
        {
          id: 'overview',
          title: 'Platform Overview',
          content: `
# CushLabs Site Analysis (v1)

CushLabs Site Analysis is an **internal, admin-only** site analysis tool.

## Core Mission
- Crawl a site starting from a URL
- Store extracted page content for inspection
- Surface high-signal issues (no noisy “SEO scoring”)
- Provide lightweight heuristics to help you decide what to fix first

## Explicit Non-Goals (v1)
- Selector-based scraping
- Client-facing reports or exports
- Real-time dashboards / WebSockets
- AI-driven scoring
          `
        },
        {
          id: 'getting-started',
          title: 'Getting Started',
          content: `
# Getting Started

## Prerequisites
- Node.js 18+ for frontend
- Python 3.11+ for backend
- Supabase account for database
- Redis server for job queues

## Quick Setup
1. **Frontend Setup**:
   \`\`\`bash
   cd frontend
   npm install
   npm start
   \`\`\`

2. **Backend Setup**:
   \`\`\`bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   \`\`\`

3. **Environment Configuration**:
   - Copy \`.env.example\` to \`.env\`
   - Configure Supabase credentials
   - Set up Redis connection
   - Add OpenAI API key (optional)

## First Crawl
1. Navigate to the Crawls page
2. Create a new crawl with a starting URL
3. Wait for the crawl to complete
4. Inspect Pages, Links, and Issues for the crawl
          `
        }
      ]
    },
    {
      id: 'architecture',
      title: 'Architecture & Tech Stack',
      icon: <Layers className="h-4 w-4" />,
      items: [
        {
          id: 'system-architecture',
          title: 'System Architecture',
          content: `
# System Architecture

## Technology Stack

### Frontend Architecture
- **Framework**: React 18 with Create React App
- **Routing**: React Router v6 with protected routes
- **Styling**: TailwindCSS + shadcn/ui components
- **State Management**: React Context API (AuthContext)
- **Authentication**: Supabase Auth with role-based access control

### Backend Architecture
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn ASGI server
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth + Row Level Security (RLS)
- **Task Queue**: Celery + Redis
- **Web Scraping**: BeautifulSoup4, Selenium, Playwright
- **AI Integration**: Disabled by default in v1 (feature-flag gated)

## Architecture Diagram

\`\`\`
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │  Supabase DB    │
│                 │    │                 │    │                 │
│ • Auth Context  │◄──►│ • API Routes    │◄──►│ • PostgreSQL    │
│ • Protected     │    │ • Auth Middleware│    │ • RLS Policies  │
│   Routes        │    │ • Validation    │    │ • User Tables   │
│ • TailwindCSS   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │  Redis + Celery │              │
         │              │                 │              │
         └──────────────►│ • Task Queue   │◄─────────────┘
                        │ • Job Processing│
                        │ • Web Scraping  │
                        └─────────────────┘
\`\`\`
          `
        },
        {
          id: 'design-principles',
          title: 'Design Principles',
          content: `
# Design Principles

## Core Principles
1. **Single Responsibility Principle (SRP)**
2. **DRY (Don't Repeat Yourself)**
3. **Separation of Concerns (SoC)**
4. **SOLID Principles**
5. **Security-First Design**

## Security Architecture
- **Row Level Security (RLS)** on all database tables
- **Admin-only access** with manual user provisioning
- **Server-side validation** for all mutations
- **Environment variable protection** for sensitive data
- **Input sanitization** for all user inputs

## Performance & Scalability
- **Atomic design** for component reusability
- **Lazy loading** for route-based code splitting
- **Efficient data fetching** with proper caching
- **Background job processing** with Celery
- **Database indexing** for optimal query performance
          `
        }
      ]
    },
    {
      id: 'api',
      title: 'API Documentation',
      icon: <Code className="h-4 w-4" />,
      items: [
        {
          id: 'api-overview',
          title: 'API Overview',
          content: `
# API Documentation

**Base URL**: \`http://localhost:8000/api/v1\`  
**API Version**: v1  
**Authentication**: Bearer Token (Supabase JWT)

## Authentication
All API endpoints require authentication using Supabase JWT tokens.

### Headers Required
\`\`\`http
Authorization: Bearer <supabase_jwt_token>
Content-Type: application/json
\`\`\`

## Core Endpoints

### Start a Crawl
\`\`\`http
POST /api/v1/crawls
\`\`\`

**Request Body:**
\`\`\`json
{
  "url": "https://example.com",
  "max_depth": 2,
  "max_pages": 100,
  "respect_robots_txt": true,
  "follow_external_links": false,
  "js_rendering": false,
  "rate_limit": 2
}
\`\`\`

**Response:**
\`\`\`json
{
  "id": "uuid-string",
  "user_id": "uuid-string",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z"
}
\`\`\`
          `
        },
        {
          id: 'api-endpoints',
          title: 'API Endpoints',
          content: `
# API Endpoints Reference

## Crawl Management

### GET /api/v1/crawls/{crawl_id}
Get crawl details.

## Data Retrieval

### GET /api/v1/crawls/{crawl_id}/pages
List pages discovered for the crawl.

### GET /api/v1/crawls/{crawl_id}/links
List links discovered for the crawl.

### GET /api/v1/crawls/{crawl_id}/issues
List detected issues for the crawl.
          `
        }
      ]
    },
    {
      id: 'features',
      title: 'Features & Usage',
      icon: <BarChart3 className="h-4 w-4" />,
      items: [
        {
          id: 'web-scraping',
          title: 'Web Scraping',
          content: `
# Web Scraping Features

## Scraping Capabilities
- **HTML Parsing**: BeautifulSoup4 for static content
- **JavaScript Rendering**: Playwright for dynamic content
- **Configurable Depth**: Control crawl depth and scope
- **Rate Limiting**: Respectful crawling with delays
- **Robots.txt Compliance**: Optional robots.txt respect

## Supported Content Types
- HTML pages and documents
- JavaScript-rendered SPAs
- XML sitemaps

## Configuration Options
- **Max Pages**: Limit total pages crawled
- **Max Depth**: Control link following depth
- **Crawl Delay**: Time between requests
- **User Agent**: Custom user agent strings
- **Include External**: Follow external links
- **JavaScript**: Enable/disable JS rendering

## Data Extraction
- Page titles and meta descriptions
- Header tags (H1, H2, H3, etc.)
- Internal and external links
          `
        },
        {
          id: 'seo-analysis',
          title: 'SEO Analysis',
          content: `
# SEO Analysis Features

## SEO Auditing
v1 focuses on **high-signal issue detection** and **lightweight heuristics**, not exhaustive scoring.

## Technical SEO
- Robots meta / indexability flags (high signal)
- Obvious broken pages (status codes)
- Thin content detection

## Content Analysis
- Content length / word count (heuristic)
- Basic page importance heuristics

## Reporting
No client-facing reports or exports in v1.
          `
        }
      ]
    },
    {
      id: 'security',
      title: 'Security & Access',
      icon: <Shield className="h-4 w-4" />,
      items: [
        {
          id: 'authentication',
          title: 'Authentication',
          content: `
# Authentication & Security

## Admin-Only Platform
This platform is designed for **admin-only access**. All users must be manually provisioned with admin privileges.

## Authentication Flow
1. **User Creation**: Manual user creation in Supabase Auth
2. **Admin Linking**: Link auth users to \`users\` table with \`is_admin\` flag
3. **Role Verification**: Check admin status on each protected route
4. **Session Management**: Supabase handles JWT tokens and sessions

## Security Layers
- **Frontend**: Protected routes with role-based access
- **Backend**: Middleware authentication validation
- **Database**: Row Level Security policies
- **API**: Input validation and sanitization

## Row Level Security (RLS)
All database tables are protected with RLS policies:

\`\`\`sql
-- Example RLS policy
CREATE POLICY "Admin only access" ON users
FOR ALL USING (auth.uid() IN (
  SELECT auth_id FROM users WHERE is_admin = true
));
\`\`\`

## Data Protection
- **Encrypted Storage**: All data encrypted at rest
- **Secure Transmission**: HTTPS/TLS for all communications
- **Environment Variables**: Sensitive data in environment variables
- **API Key Management**: Secure API key storage and rotation
- **Input Sanitization**: All user inputs validated and sanitized
          `
        },
        {
          id: 'user-management',
          title: 'User Management',
          content: `
# User Management

## Admin User Creation
Since this is an admin-only platform, users must be manually created:

1. **Supabase Auth Console**:
   - Create user in Supabase Auth dashboard
   - Set initial password and email

2. **Database Linking**:
   - Add user record to \`users\` table
   - Set \`is_admin = true\`
   - Link via \`auth_id\` field

3. **Role Assignment**:
   - All users have admin privileges
   - No role hierarchy currently implemented
   - Future: Super admin vs. regular admin roles

## User Profile Management
- **Profile Updates**: Users can update their own profiles
- **Password Changes**: Secure password change flow
- **Account Information**: View creation date, last login
- **Activity Tracking**: Audit log of user actions

## Security Best Practices
- **Strong Passwords**: Enforce password complexity
- **Session Management**: Automatic session expiration
- **Activity Monitoring**: Track user actions and access
- **Access Logging**: Comprehensive audit trails
- **Regular Reviews**: Periodic access reviews and cleanup
          `
        }
      ]
    },
    {
      id: 'configuration',
      title: 'Configuration',
      icon: <Settings className="h-4 w-4" />,
      items: [
        {
          id: 'environment-setup',
          title: 'Environment Setup',
          content: `
# Environment Configuration

## Frontend Environment Variables
Create \`.env\` file in frontend directory:

\`\`\`bash
# Supabase Configuration
REACT_APP_SUPABASE_URL=your_supabase_project_url
REACT_APP_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key

# API Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1

# Optional: Analytics
REACT_APP_GA_TRACKING_ID=your_google_analytics_id
\`\`\`

Note: Legacy REACT_APP_SUPABASE_ANON_KEY is still supported for backwards compatibility.

## Backend Environment Variables
Create \`.env\` file in backend directory:

\`\`\`bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SECRET_KEY=your_supabase_secret_key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Feature flags (default off in v1)
ENABLE_BATCH_CRAWLS=false
ENABLE_SELECTOR_SCRAPING=false
ENABLE_SEO_AUDIT=false
ENABLE_LLM=false

# Storage Configuration
STORAGE_DIR=./storage
\`\`\`

## Database Setup
1. **Create Supabase Project**: Sign up at supabase.com
2. **Run Migrations**: Execute SQL files in \`db_sql/\` directory
3. **Enable RLS**: Ensure Row Level Security is enabled
4. **Create Policies**: Apply security policies for admin access
          `
        },
        {
          id: 'crawl-settings',
          title: 'Crawl Settings',
          content: `
# Crawl Configuration

## Default Settings
Configure default crawl parameters in the backend:

\`\`\`python
# Default crawl configuration
DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_PAGES = 100
DEFAULT_CRAWL_DELAY = 1  # seconds
DEFAULT_USER_AGENT = "AAA-WebScraper/1.0"
DEFAULT_TIMEOUT = 30     # seconds
\`\`\`

## Per-Crawl Settings
Each crawl can be customized with:

- **URL**: Starting URL for the crawl
- **Max Depth**: How many levels deep to follow links
- **Max Pages**: Maximum number of pages to crawl
- **Include External**: Whether to follow external links
- **JavaScript Enabled**: Use Playwright for JS rendering
- **Crawl Delay**: Time between requests (be respectful)
- **Respect Robots**: Honor robots.txt directives
- **User Agent**: Custom user agent string

## Storage Settings
Control what data is stored:

- **HTML Snapshots**: Store full HTML content
- **Screenshots**: Capture page screenshots
- **Metadata Only**: Store only analysis results
- **Retention Period**: How long to keep crawl data

## Performance Tuning
- **Concurrency**: Number of parallel requests
- **Rate Limiting**: Requests per second limits
- **Memory Limits**: Maximum memory usage per crawl
- **Timeout Settings**: Request and total crawl timeouts
          `
        }
      ]
    }
  ];

  const getActiveContent = () => {
    for (const section of docSections) {
      const item = section.items.find(item => item.id === activeSection);
      if (item) return item.content;
    }
    return '';
  };

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering - in a real app, use a proper markdown parser
    return content.split('\n').map((line, index) => {
      if (line.startsWith('# ')) {
        return <h1 key={index} className="text-3xl font-bold mt-8 mb-4 text-gray-900">{line.slice(2)}</h1>;
      }
      if (line.startsWith('## ')) {
        return <h2 key={index} className="text-2xl font-bold mt-6 mb-3 text-gray-800">{line.slice(3)}</h2>;
      }
      if (line.startsWith('### ')) {
        return <h3 key={index} className="text-xl font-bold mt-4 mb-2 text-gray-700">{line.slice(4)}</h3>;
      }
      if (line.startsWith('```')) {
        return <div key={index} className="bg-gray-100 p-4 rounded-md font-mono text-sm my-4 overflow-x-auto border">{line.slice(3)}</div>;
      }
      if (line.startsWith('- ')) {
        return <li key={index} className="ml-6 mb-1 text-gray-700">{line.slice(2)}</li>;
      }
      if (line.includes('**') && line.includes('**')) {
        const parts = line.split('**');
        return (
          <p key={index} className="mb-3 text-gray-700 leading-relaxed">
            {parts.map((part, i) => i % 2 === 1 ? <strong key={i}>{part}</strong> : part)}
          </p>
        );
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index} className="mb-3 text-gray-700 leading-relaxed">{line}</p>;
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex-grow">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Documentation</h1>
            <p className="text-xl text-gray-600">Guide to the AI WebScraper by CushLabs.ai</p>
          </div>

          <div className="flex gap-8">
            {/* Sidebar Navigation */}
            <div className="w-80 bg-white rounded-lg shadow-sm border p-6">
              <nav className="space-y-2">
                {docSections.map((section) => (
                  <div key={section.id}>
                    <button
                      onClick={() => toggleSection(section.id)}
                      className="flex items-center justify-between w-full p-3 text-left rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {section.icon}
                        <span className="font-medium text-gray-900">{section.title}</span>
                      </div>
                      {expandedSections.has(section.id) ?
                        <ChevronDown className="h-4 w-4 text-gray-500" /> :
                        <ChevronRight className="h-4 w-4 text-gray-500" />
                      }
                    </button>

                    {expandedSections.has(section.id) && (
                      <div className="ml-6 mt-2 space-y-1">
                        {section.items.map((item) => (
                          <button
                            key={item.id}
                            onClick={() => setActiveSection(item.id)}
                            className={`block w-full text-left p-2 rounded-md text-sm transition-colors ${
                              activeSection === item.id
                                ? 'bg-blue-50 text-blue-700 font-medium'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                            }`}
                          >
                            {item.title}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 bg-white rounded-lg shadow-sm border p-8">
              <div className="prose prose-lg max-w-none">
                {renderMarkdown(getActiveContent())}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default DocsPage;
