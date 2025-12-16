# AAA Web Scraper - User Journey Documentation

## Overview

The AAA Web Scraper is an **admin-only** web scraping and site auditing platform designed for technical users to crawl websites, analyze content, and generate comprehensive reports. The platform uses Supabase for authentication and data storage, ensuring secure access control.

## Authentication System

### Login Process
- **Admin-Only Access**: This is not a public application - only authorized administrators can access the platform
- **Supabase Authentication**: Uses email/password authentication through Supabase
- **Session Management**: Maintains user sessions with automatic token refresh
- **Role-Based Access**: Distinguishes between regular admins and super admins

### User Roles
1. **Admin**: Can access most features, create crawls, view reports
2. **Super Admin**: Full access including user management and system settings

## User Journey Flow

### 1. Authentication Flow
```
Landing Page (/) → Login Page (/login) → Dashboard (/dashboard)
```

**Step 1: Access Application**
- User navigates to the application URL
- If not authenticated, automatically redirected to `/login`

**Step 2: Admin Login**
- Enter email address and password
- System validates credentials through Supabase
- On success: Redirect to Dashboard
- On failure: Display error message

**Step 3: Session Validation**
- System checks user role (admin/super admin)
- Establishes authenticated session
- Enables access to protected routes

### 2. Main Application Workflow

#### Dashboard (/dashboard)
- **Purpose**: Central hub showing system overview
- **Features**: 
  - Recent activity summary
  - Quick access to main functions
  - System status indicators

#### Crawling Workflow

**Option A: Individual Crawls (/crawls)**
```
Crawls Page → Create New Crawl → Configure Settings → Start Crawl → Monitor Progress → View Results
```

**Option B: Batch Operations (/batches)**
```
Batches Page → Create Batch → Add Multiple URLs → Configure Batch Settings → Execute Batch → Monitor All Crawls
```

**Crawl Configuration Options:**
- **Target URL**: Starting point for crawling
- **Max Depth**: How deep to crawl (levels of links to follow)
- **Max Pages**: Maximum number of pages to crawl
- **JavaScript Rendering**: Enable for SPA/dynamic content
- **Robots.txt Compliance**: Respect or ignore robots.txt
- **External Links**: Follow links to external domains
- **Rate Limiting**: Control crawling speed
- **Custom User Agent**: Identify the crawler

#### Content Analysis & Reporting

**Reports Dashboard (/reports)**
- **Analytics Overview**: Summary cards with key metrics
- **Crawl Status Distribution**: Visual breakdown of crawl statuses
- **Issue Detection**: Top issues found across crawls
- **Recent Activity**: Timeline of recent crawling activity
- **Date Filtering**: Filter reports by time period

**Individual Crawl Details (/crawls/:id)**
- **Crawl Metadata**: Configuration, status, timing
- **Page-by-Page Results**: Detailed analysis of each crawled page
- **Link Analysis**: Internal/external link mapping
- **SEO Insights**: Meta tags, titles, descriptions
- **Error Reporting**: Broken links, failed requests
- **Content Summaries**: AI-generated page summaries

#### Administrative Functions

**User Management (/users)** - Super Admin Only
- **User List**: View all admin users
- **Role Management**: Assign admin/super admin roles
- **Account Creation**: Add new admin users
- **Access Control**: Enable/disable user accounts

**Profile Management (/profile)**
- **Account Details**: View user information
- **Password Change**: Update login credentials
- **Session History**: View login activity

### 3. Advanced Features

#### Scraping Interface (/scrape)
- **Quick Scrape**: Single-page scraping tool
- **Custom Parameters**: Advanced configuration options
- **Real-time Results**: Live preview of scraped content

#### Data Export & Integration
- **Export Formats**: JSON, CSV, XML
- **API Access**: RESTful API for programmatic access
- **Webhook Integration**: Real-time notifications

## Technical Workflow

### Data Flow
1. **Input**: User provides URLs and crawling parameters
2. **Queue**: Jobs added to Redis queue for processing
3. **Processing**: FastAPI backend executes crawling tasks
4. **Storage**: Results stored in Supabase database
5. **Analysis**: Content analysis and SEO extraction
6. **Presentation**: Results displayed in React frontend

### Security Model
- **Row Level Security (RLS)**: Database-level access control
- **JWT Tokens**: Secure API authentication
- **Input Sanitization**: Protection against malicious inputs
- **Rate Limiting**: Prevent abuse and overload

## Error Handling & Edge Cases

### Common Scenarios
- **Invalid URLs**: Validation and error messaging
- **Crawl Failures**: Retry mechanisms and failure reporting
- **Timeout Handling**: Configurable timeout limits
- **Resource Limits**: Memory and processing constraints

### User Guidance
- **Progress Indicators**: Real-time crawl status updates
- **Error Messages**: Clear, actionable error descriptions
- **Help Documentation**: Contextual help and tooltips

## Navigation Structure

```
Header Navigation:
├── Dashboard - Main overview
├── Crawls - Individual crawl management
├── Batches - Bulk crawl operations
├── Reports - Analytics and insights
├── Users - Admin user management (Super Admin only)
└── Profile - User account settings

Additional Routes:
├── /scrape - Quick scraping tool
├── /privacy - Privacy policy
├── /terms - Terms of service
└── /login - Authentication page
```

## Success Metrics

### User Experience
- **Time to First Crawl**: How quickly new users can start their first crawl
- **Task Completion Rate**: Percentage of successfully completed crawls
- **Error Recovery**: How effectively users handle and resolve errors

### System Performance
- **Crawl Success Rate**: Percentage of successful crawl operations
- **Processing Speed**: Average time per page crawled
- **System Uptime**: Platform availability metrics

## Future Enhancements

### Planned Features
- **Scheduled Crawling**: Automated recurring crawls
- **Advanced Filtering**: Content-based filtering options
- **Collaboration Tools**: Team-based crawl management
- **Custom Integrations**: Third-party tool connections

### User Experience Improvements
- **Onboarding Flow**: Guided setup for new admins
- **Bulk Operations**: Enhanced batch processing capabilities
- **Mobile Responsiveness**: Improved mobile interface
- **Real-time Notifications**: Live updates and alerts

---

## Getting Started

### For New Admins
1. **Receive Credentials**: Admin provides login credentials
2. **First Login**: Access the platform at the provided URL
3. **Explore Dashboard**: Familiarize yourself with the interface
4. **Test Crawl**: Start with a simple single-page crawl
5. **Review Results**: Understand the output format and insights

### Best Practices
- **Start Small**: Begin with single pages before batch operations
- **Monitor Resources**: Be mindful of crawling impact on target sites
- **Regular Reviews**: Check crawl results and adjust parameters
- **Stay Updated**: Keep informed about platform updates and features

This documentation serves as a comprehensive guide to understanding and using the AAA Web Scraper platform effectively.
