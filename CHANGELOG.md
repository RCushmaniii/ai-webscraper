# Changelog

All notable changes to the AI WebScraper project will be documented in this file.

## [1.0.0] - 2025-12-27

### Added

- **World-Class Dashboard**: Complete dashboard redesign with stats cards, recent crawls, and quick actions

  - Stats cards showing total crawls, completed, active, and pages crawled
  - Recent crawls section displaying top 5 most recent crawls sorted by date
  - Quick actions sidebar with direct navigation
  - Failed crawls alert widget
  - Responsive grid layout with modern card design

- **Stale Crawl Monitoring System**: Comprehensive solution to prevent stuck crawls

  - Background monitoring service that runs every 10 minutes
  - Automatic detection and marking of stale crawls as failed
  - Configurable timeouts: 30min (running), 60min (queued/pending)
  - Manual "Mark as Failed" button on UI for stuck crawls
  - API endpoint: `POST /crawls/{id}/mark-failed`
  - Integrated into FastAPI startup lifecycle

- **Dedicated New Crawl Page**: Separated crawl creation into its own route

  - New route: `/crawls/new`
  - Admin-only access control
  - Clean, focused form experience
  - Removed inline form from crawls list page

- **Navigation Improvements**
  - "New Crawl" buttons now navigate to dedicated form page
  - "View All" link on dashboard properly navigates to crawls list
  - Improved UX flow throughout application

### Fixed

- **TypeScript Type Errors**: Updated Crawl interface to include all valid status values
  - Added: 'pending', 'running', 'cancelled' to status union type
  - Matches database constraint exactly
- **Stuck Crawl Issue**: Fixed immediate stuck crawl from 11:23 AM

  - Was stuck in "running" status for 594 minutes
  - Marked as failed with appropriate error message

- **Dashboard Recent Crawls**: Fixed population and sorting
  - Now properly sorts by `created_at` descending
  - Shows exactly 5 most recent crawls
  - Displays timestamp and status for each crawl

### Changed

- **CrawlsPage Refactoring**: Removed inline form, simplified component

  - Removed form state management
  - Removed query parameter handling
  - Cleaner, more maintainable code
  - All "New Crawl" actions now use Link to `/crawls/new`

- **API Service**: Added `markCrawlFailed` method
  - Allows manual marking of stuck crawls as failed
  - Includes proper error handling

### Technical Improvements

- Added background task scheduler using FastAPI lifespan events
- Created reusable crawl monitoring service module
- Improved error logging and monitoring
- Added health check endpoint with monitoring status
- Created comprehensive deployment documentation

### Files Added

- `backend/app/services/crawl_monitor.py` - Stale crawl monitoring service
- `backend/fix_stale_crawls.py` - Manual stale crawl checker script
- `frontend/src/pages/CrawlNewPage.tsx` - Dedicated new crawl form page
- `DEPLOYMENT_PLAN.md` - Comprehensive deployment guide
- `CHANGELOG.md` - This file

### Files Modified

- `backend/app/main.py` - Added background monitoring task
- `backend/app/api/routes/crawls.py` - Added mark-failed endpoint
- `frontend/src/pages/DashboardPage.tsx` - Complete redesign
- `frontend/src/pages/CrawlsPage.tsx` - Removed inline form
- `frontend/src/pages/CrawlDetailPage.tsx` - Added mark-failed button
- `frontend/src/services/api.ts` - Added markCrawlFailed method, updated status types
- `frontend/src/App.tsx` - Added /crawls/new route

### Database Changes

- Updated crawl status constraint to include all valid values
- See `fix_status_constraint.sql` for migration

---

## Future Enhancements (Planned)

### High Priority

- Email notifications for crawl completion/failure
- Scheduled/recurring crawls (cron-like functionality)
- Export functionality (CSV, JSON, PDF reports)
- Advanced filtering and search on crawls list

### Medium Priority

- Crawl comparison tools
- Historical analytics and trends
- Webhook support for crawl events
- API rate limiting and quotas

### Low Priority

- Dark mode support
- Multi-language support (i18n)
- Crawl templates/presets
- Team collaboration features

---

## Version History

- **v1.0.0** (2025-12-27) - Initial production release with dashboard improvements and stale crawl monitoring
