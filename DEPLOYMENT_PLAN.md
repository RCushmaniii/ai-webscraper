# AI WebScraper - Deployment Plan

## Overview

This document outlines the deployment strategy for the AI WebScraper application, including pre-deployment checklist, deployment steps, and post-deployment verification.

---

## Pre-Deployment Checklist

### 1. Database Migrations

- [ ] Run status constraint fix: `fix_status_constraint.sql`
- [ ] Verify all RLS policies are in place
- [ ] Test database connections from both local and production environments
- [ ] Backup current database state

### 2. Environment Variables

Ensure the following are configured in production:

**Backend (.env)**

```
SUPABASE_URL=<production_supabase_url>
SUPABASE_KEY=<production_supabase_anon_key>
SUPABASE_SERVICE_ROLE_KEY=<production_service_role_key>
JWT_SECRET=<secure_random_secret>
BACKEND_CORS_ORIGINS=["https://your-frontend-domain.com"]
```

**Frontend (.env)**

```
REACT_APP_API_URL=https://your-backend-domain.com/api/v1
REACT_APP_SUPABASE_URL=<production_supabase_url>
REACT_APP_SUPABASE_ANON_KEY=<production_supabase_anon_key>
```

### 3. Code Quality Checks

- [ ] Run TypeScript type checking: `npm run build` (frontend)
- [ ] Run Python linting: `flake8` or `pylint` (backend)
- [ ] Test all critical user flows locally
- [ ] Verify no console errors in browser

### 4. Security Review

- [ ] Ensure no hardcoded secrets in code
- [ ] Verify RLS policies are enabled on all tables
- [ ] Check CORS settings are restrictive
- [ ] Review authentication flows
- [ ] Verify admin-only routes are protected

---

## Deployment Steps

### Phase 1: Backend Deployment

#### Option A: Deploy to Railway/Render/Fly.io

1. **Create new service** on your platform of choice
2. **Connect GitHub repository**
3. **Configure build settings**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Root directory: `backend`
4. **Set environment variables** (see checklist above)
5. **Deploy and verify** health endpoint: `https://your-backend.com/health`

#### Option B: Deploy to AWS/GCP/Azure

1. **Create container image**:
   ```bash
   cd backend
   docker build -t ai-webscraper-backend .
   ```
2. **Push to container registry**
3. **Deploy to container service** (ECS, Cloud Run, Container Apps)
4. **Configure load balancer** and SSL certificate
5. **Set environment variables**
6. **Verify health endpoint**

### Phase 2: Frontend Deployment

#### Option A: Deploy to Vercel/Netlify

1. **Connect GitHub repository**
2. **Configure build settings**:
   - Build command: `npm run build`
   - Publish directory: `build`
   - Root directory: `frontend`
3. **Set environment variables** (see checklist above)
4. **Deploy and verify**

#### Option B: Deploy to AWS S3 + CloudFront

1. **Build production bundle**:
   ```bash
   cd frontend
   npm run build
   ```
2. **Upload to S3 bucket**
3. **Configure CloudFront distribution**
4. **Set up SSL certificate**
5. **Configure custom domain**

### Phase 3: Database Setup

1. **Run migrations** on production Supabase instance:
   ```sql
   -- Run fix_status_constraint.sql
   -- Verify all tables and policies
   ```
2. **Create initial admin user** (if needed)
3. **Test database connectivity** from backend

---

## Post-Deployment Verification

### 1. Smoke Tests

- [ ] Visit homepage - loads correctly
- [ ] Sign up new user - works
- [ ] Sign in - works
- [ ] Dashboard loads with correct data
- [ ] Create new crawl - works
- [ ] View crawl details - works
- [ ] Mark stuck crawl as failed - works
- [ ] Delete crawl - works
- [ ] Admin panel accessible (admin users only)

### 2. Monitoring Setup

- [ ] Set up application monitoring (Sentry, LogRocket, etc.)
- [ ] Configure error alerting
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Monitor background task logs (stale crawl checker)

### 3. Performance Checks

- [ ] Verify page load times < 3 seconds
- [ ] Check API response times < 500ms
- [ ] Test with multiple concurrent users
- [ ] Verify crawl jobs complete successfully

---

## Rollback Plan

If issues arise post-deployment:

1. **Frontend Issues**:

   - Revert to previous deployment via platform dashboard
   - Or redeploy previous Git commit

2. **Backend Issues**:

   - Revert to previous deployment
   - Check logs for errors
   - Verify environment variables

3. **Database Issues**:
   - Restore from backup
   - Revert migration if needed

---

## Monitoring & Maintenance

### Daily

- Check error logs for critical issues
- Monitor crawl success/failure rates

### Weekly

- Review stale crawl logs
- Check database performance
- Review user feedback

### Monthly

- Update dependencies
- Review security patches
- Optimize database queries if needed

---

## GitHub Sync Checklist

Before deployment, ensure all code is synced:

```bash
# Check current status
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add dashboard improvements, stale crawl monitoring, and deployment setup"

# Push to main branch
git push origin main

# Create deployment tag
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0
```

---

## Key Features Deployed

### ✅ Dashboard Enhancements

- Stats cards showing total/completed/active crawls and pages
- Recent crawls section (top 5, sorted by date)
- Quick actions sidebar
- Failed crawls alert widget

### ✅ Stale Crawl Monitoring

- Background task runs every 10 minutes
- Automatically marks stuck crawls as failed
- Manual "Mark as Failed" button on UI
- Timeouts: 30min (running), 60min (queued/pending)

### ✅ Navigation Improvements

- "New Crawl" button opens form directly
- Dedicated `/crawls/new` route
- Improved UX flow throughout app

### ✅ Bug Fixes

- Fixed TypeScript type errors for crawl statuses
- Fixed RLS policy issues
- Improved error handling

---

## Support & Troubleshooting

### Common Issues

**Issue**: Crawls stuck in running state
**Solution**: Background monitor will auto-fix, or use "Mark as Failed" button

**Issue**: CORS errors
**Solution**: Verify `BACKEND_CORS_ORIGINS` includes frontend domain

**Issue**: Authentication failures
**Solution**: Check Supabase keys and JWT secret are correct

**Issue**: Database connection errors
**Solution**: Verify Supabase URL and service role key

---

## Next Steps After Deployment

1. Monitor application for 24-48 hours
2. Gather user feedback
3. Plan next iteration of features
4. Set up CI/CD pipeline for automated deployments
5. Consider adding:
   - Email notifications for crawl completion
   - Scheduled crawls (cron-like functionality)
   - Export functionality (CSV, JSON)
   - Advanced filtering and search
   - Crawl comparison tools

---

**Deployment Date**: ******\_******
**Deployed By**: ******\_******
**Version**: v1.0.0
**Status**: ☐ Pending ☐ In Progress ☐ Complete
