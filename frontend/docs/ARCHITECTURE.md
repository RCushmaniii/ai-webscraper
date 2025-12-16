# AAA Web Scraper - Architecture & Tech Stack

## 🏗️ System Overview

The AAA Web Scraper is an **admin-only web scraping and site auditing platform** designed for comprehensive website analysis, SEO auditing, and performance monitoring.

### Core Mission
- Crawl HTML and JavaScript-rendered pages with configurable depth
- Generate detailed per-page summaries and comprehensive site audits
- Detect broken links and extract SEO metadata
- Provide actionable insights for website optimization

---

## 🛠️ Technology Stack

### Frontend Architecture
- **Framework**: React 18 with Create React App
- **Routing**: React Router v6 with protected routes
- **Styling**: TailwindCSS + shadcn/ui components
- **State Management**: React Context API (AuthContext)
- **Authentication**: Supabase Auth with role-based access control
- **Build Tool**: Create React App (CRA)
- **Language**: TypeScript

### Backend Architecture
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn ASGI server
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth + Row Level Security (RLS)
- **Task Queue**: Celery + Redis
- **Web Scraping**: 
  - BeautifulSoup4 for HTML parsing
  - Selenium for JavaScript-rendered content
  - HTTPX for HTTP requests
- **File Storage**: Supabase Storage

### Infrastructure & DevOps
- **Database**: Supabase PostgreSQL with RLS policies
- **Authentication**: Supabase Auth (admin-only)
- **Caching**: Redis for task queues and session management
- **Environment**: Docker support for containerization

---

## 🏛️ Architecture Principles

Following strategic development principles and modern best practices:

### Core Design Principles
1. **Single Responsibility Principle (SRP)**
2. **DRY (Don't Repeat Yourself)**
3. **Separation of Concerns (SoC)**
4. **SOLID Principles**
5. **Security-First Design**

### Security Architecture
- **Row Level Security (RLS)** on all database tables
- **Admin-only access** with manual user provisioning
- **Server-side validation** for all mutations
- **Environment variable protection** for sensitive data
- **Input sanitization** for all user inputs

### Performance & Scalability
- **Atomic design** for component reusability
- **Lazy loading** for route-based code splitting
- **Efficient data fetching** with proper caching
- **Background job processing** with Celery
- **Database indexing** for optimal query performance

---

## 📊 System Architecture Diagram

```
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
```

---

## 🗂️ Project Structure

```
aaa-webscraper/
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── ui/            # shadcn/ui base components
│   │   │   └── layout/        # Layout components
│   │   ├── contexts/          # React contexts (Auth, etc.)
│   │   ├── pages/             # Page components
│   │   ├── lib/               # Utilities and configurations
│   │   └── utils/             # Helper functions
│   ├── docs/                  # Documentation files
│   ├── db_sql/               # Database schema and fixes
│   └── public/               # Static assets
│
├── backend/                     # FastAPI backend application
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   ├── core/             # Core configurations
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic services
│   │   └── utils/            # Backend utilities
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Container configuration
│
└── README.md                   # Project documentation
```

---

## 🔐 Authentication & Security

### Authentication Flow
1. **Admin Creation**: Manual user creation in Supabase Auth
2. **User Linking**: Link auth users to `users` table with `is_admin` flag
3. **Role Verification**: Check admin status on each protected route
4. **Session Management**: Supabase handles JWT tokens and sessions

### Security Layers
- **Frontend**: Protected routes with role-based access
- **Backend**: Middleware authentication validation
- **Database**: Row Level Security policies
- **API**: Input validation and sanitization

---

## 🔄 Data Flow Architecture

### Web Scraping Workflow
```
User Request → FastAPI Endpoint → Celery Task → Web Scraper
     ↓              ↓                ↓             ↓
Database ← API Response ← Task Result ← Scraped Data
```

### Authentication Flow
```
Login Form → Supabase Auth → JWT Token → Protected Routes
     ↓            ↓             ↓            ↓
User Context ← Auth State ← Token Validation ← Route Access
```

---

## 📋 Database Schema

### Core Tables
- **users**: User profiles and admin flags
- **batches**: Scraping job batches
- **crawls**: Individual crawl sessions
- **pages**: Scraped page data and metadata
- **links**: Link relationships and status
- **tasks**: Background job tracking

### Security Policies
- All tables protected with RLS
- Admin-only access enforcement
- Authenticated user requirements
- Proper foreign key relationships

---

## 🚀 Development Workflow

### Environment Setup
1. **Frontend**: React development server on port 3000
2. **Backend**: FastAPI server on port 8000
3. **Database**: Supabase cloud instance
4. **Redis**: Local Redis server for task queue

### Build Process
1. **Development**: Hot reload for both frontend and backend
2. **Testing**: Component and API endpoint testing
3. **Production**: Optimized builds with proper environment configs
4. **Deployment**: Docker containers for consistent environments

---

## 📈 Scalability Considerations

### Performance Optimization
- **Component Memoization**: React.memo for expensive components
- **Code Splitting**: Route-based lazy loading
- **Database Indexing**: Optimized queries with proper indexes
- **Caching Strategy**: Redis for frequently accessed data

### Future Enhancements
- **Multi-tenant Support**: Extend for multiple organizations
- **Real-time Updates**: WebSocket integration for live progress
- **Advanced Analytics**: Enhanced reporting and visualization
- **API Rate Limiting**: Protect against abuse and overuse

---

## 🔧 Configuration Management

### Environment Variables
- **Frontend**: `REACT_APP_` prefixed variables
- **Backend**: Standard environment variables
- **Database**: Supabase connection strings
- **Security**: API keys and service roles

### Deployment Configurations
- **Development**: Local environment with hot reload
- **Staging**: Pre-production testing environment  
- **Production**: Optimized builds with security hardening

---

This architecture ensures a robust, scalable, and secure platform for web scraping and site auditing while maintaining clean code principles and modern development practices.
