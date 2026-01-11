# Security Setup - Quick Start Guide

This guide walks you through setting up and testing the three security features.

---

## Prerequisites

- [x] Supabase project set up
- [x] Backend running locally
- [x] Environment variables configured in `.env`

---

## Step 1: Run RLS Migration

### Option A: Via Supabase Dashboard (Recommended for first time)

1. Open Supabase Dashboard
2. Go to **SQL Editor**
3. Create a new query
4. Copy the entire contents of `database/migrations/004_enhance_rls_policies.sql`
5. Paste into SQL Editor
6. Click **Run**
7. Check the output of `test_rls_policies()` at the bottom:

Expected output:
```
test_name              | passed | details
-----------------------+--------+--------------------------------
RLS Enabled Check      | true   | All user tables have RLS enabled
Policies Exist Check   | true   | Found 18 policies
```

### Option B: Via Command Line (PostgreSQL CLI)

```bash
# Make sure psql is installed
psql --version

# Connect to your Supabase database
# Get connection string from: Supabase Dashboard > Settings > Database > Connection String (Direct)
psql "postgresql://postgres:[YOUR-PASSWORD]@db.your-project.supabase.co:5432/postgres" \
  -f database/migrations/004_enhance_rls_policies.sql

# Check the output - should show tests passing
```

---

## Step 2: Test RLS Policies

### Test 2.1: Logged-in User Can Access Own Data

1. Log in to your app via the frontend
2. Open browser DevTools > Network tab
3. Navigate to dashboard
4. Check the request to `/api/v1/crawls`
5. Should see your own crawls (if any)

**Manual SQL Test:**
```sql
-- In Supabase SQL Editor
-- Make sure you're authenticated (run from frontend that's logged in)

-- Get your user ID
SELECT auth.uid();

-- Should return your crawls
SELECT * FROM crawls WHERE user_id = auth.uid();

-- Should return 0 rows (even if other users have crawls)
SELECT * FROM crawls WHERE user_id != auth.uid();
```

### Test 2.2: Unauthenticated User CANNOT Access Data

```bash
# Try to access crawls without auth token
curl http://localhost:8000/api/v1/crawls

# Should return 401 Unauthorized or empty results
```

### Test 2.3: Insert Attack FAILS

```sql
-- In Supabase SQL Editor (while logged in as User A)

-- Try to create a crawl for a different user
INSERT INTO crawls (
  user_id,
  url,
  name,
  status,
  max_depth,
  max_pages,
  respect_robots_txt,
  follow_external_links,
  js_rendering,
  rate_limit,
  created_at,
  updated_at
) VALUES (
  'some-other-user-id-here',  -- Different user!
  'https://example.com',
  'Test Crawl',
  'pending',
  2,
  100,
  true,
  false,
  false,
  2,
  now(),
  now()
);

-- Expected error:
-- new row violates row-level security policy for table "crawls"
```

---

## Step 3: Test Rate Limiting

### Test 3.1: Check Rate Limit Configuration

```bash
# Start backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload

# Backend should start with rate limiting middleware active
# Look for log: "Started background stale crawl monitoring..."
```

### Test 3.2: Trigger Rate Limit (Free Tier)

```bash
# Make 15 requests in quick succession (Free tier limit is 10/minute)
for i in {1..15}; do
  curl -X GET http://localhost:8000/api/v1/crawls \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  echo "Request $i"
done

# Requests 1-10 should succeed (200 OK)
# Requests 11-15 should fail (429 Too Many Requests)
```

Expected 429 response:
```json
{
  "detail": "Rate limit exceeded: Too many requests per minute. Please slow down. Upgrade to Pro ($29/month) for much higher limits.",
  "retry_after": 60,
  "upgrade_url": "/pricing"
}
```

### Test 3.3: Check Rate Limit Headers

```bash
# Check rate limit info in response headers
curl -v http://localhost:8000/api/v1/crawls \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Should see headers:
# X-RateLimit-Limit: 10
# X-RateLimit-Remaining: 9
# Retry-After: 60 (if rate limit hit)
```

---

## Step 4: Test CORS Configuration

### Test 4.1: Development CORS (Localhost)

```bash
# Test from allowed origin (localhost:3000)
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8000/api/v1/crawls

# Should return:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Credentials: true
```

### Test 4.2: Production CORS (When Deployed)

First, update your production domains in `backend/app/core/config.py`:

```python
# Replace placeholder domains with YOUR actual domains
_PROD_CORS_ORIGINS: list[str] = [
    "https://yourdomain.com",           # Your actual domain
    "https://www.yourdomain.com",       # www subdomain
    "https://app.yourdomain.com",       # App subdomain
]
```

Then set environment:

```bash
# In production .env
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Restart backend
```

Test from browser:

```javascript
// On https://yourdomain.com - should work
fetch('https://api.yourdomain.com/api/v1/crawls', {
  credentials: 'include'
})
.then(r => r.json())
.then(console.log);

// On https://evil.com - should fail with CORS error
fetch('https://api.yourdomain.com/api/v1/crawls', {
  credentials: 'include'
})
.then(r => r.json())
.catch(err => console.error('CORS blocked:', err));
```

### Test 4.3: Check Environment-Specific CORS

```python
# Test in Python
from app.core.config import settings

# Check current environment
print(f"Environment: {settings.ENVIRONMENT}")

# Check CORS origins
print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")

# Development should show localhost:3000, localhost:5173, etc.
# Production should show only your actual domains
```

---

## Step 5: Integration Test (All Features Together)

### Complete User Flow Test

1. **User signs up**
   ```bash
   POST /api/v1/auth/signup
   # RLS: Creates user record (user can only create their own)
   # Rate Limit: Counts toward requests/minute
   # CORS: Only allowed from approved domains
   ```

2. **User creates crawl**
   ```bash
   POST /api/v1/crawls
   # RLS: WITH CHECK ensures user_id = auth.uid()
   # Rate Limit: Checks crawls_per_month (Free: 5/month)
   # CORS: Validated
   ```

3. **User views crawls**
   ```bash
   GET /api/v1/crawls
   # RLS: USING clause only returns user's own crawls
   # Rate Limit: Increments counter
   # CORS: Validated
   ```

4. **User tries to access another user's crawl**
   ```bash
   GET /api/v1/crawls/{other-user-crawl-id}
   # RLS: Returns 404 (policy prevents seeing it even exists)
   # Rate Limit: Still counts request
   # CORS: Validated
   ```

5. **User hits rate limit**
   ```bash
   # 11th request in 1 minute (Free tier)
   GET /api/v1/crawls
   # RLS: Not checked (blocked by rate limiter first)
   # Rate Limit: Returns 429 Too Many Requests
   # CORS: Validated
   ```

---

## Troubleshooting

### Problem: RLS policies not working

**Symptom:** Users can see other users' data

**Fix:**
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'crawls', 'pages', 'links', 'images', 'seo_metadata', 'issues', 'summaries');

-- If rowsecurity is false, enable it
ALTER TABLE crawls ENABLE ROW LEVEL SECURITY;

-- Check if policies exist
SELECT * FROM pg_policies WHERE schemaname = 'public';

-- Re-run migration if needed
```

### Problem: Rate limiting not working

**Symptom:** Can make unlimited requests

**Fix:**
```python
# Check if middleware is loaded
# In backend/app/main.py, verify this line exists:
app.middleware("http")(rate_limit_middleware)

# Check logs for rate limit checks
# Should see: "Rate limit OK for user {user_id}: {current}/{limit} rpm"

# Verify user_id is being set
# Add debug logging in rate_limit_middleware
```

### Problem: CORS errors in browser

**Symptom:** "CORS policy: No 'Access-Control-Allow-Origin' header"

**Fix:**
```python
# Check CORS origins configuration
from app.core.config import settings
print(settings.BACKEND_CORS_ORIGINS)

# Make sure your frontend origin is in the list
# Development: Should include http://localhost:3000
# Production: Should include https://yourdomain.com

# Check environment
print(settings.ENVIRONMENT)  # Should be 'development' or 'production'

# If using environment variable:
# Set CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Problem: Rate limit storage growing too large

**Symptom:** Memory usage increasing over time

**Fix:**
```python
# In-memory rate limiter has cleanup mechanism
# It runs every hour (cleanup_interval = 3600)

# To manually trigger cleanup:
from app.middleware.rate_limiter import _rate_limiter
_rate_limiter._cleanup_old_entries()

# For production, implement Redis-based limiter
# See backend/app/middleware/rate_limiter.py RedisRateLimiter class
```

---

## Environment Configuration

### Development `.env`

```bash
# Environment
ENVIRONMENT=development

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# CORS (optional, uses defaults if not set)
# CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# SSL (optional, auto-detected)
# SUPABASE_SSL_CERT_PATH=./backend/certs/prod-ca-2021.crt
```

### Production `.env`

```bash
# Environment
ENVIRONMENT=production

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# CORS (CRITICAL: Set your actual domains!)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com

# SSL
SUPABASE_SSL_CERT_PATH=/opt/ai-webscraper/certs/prod-ca-2021.crt

# Redis (for production rate limiting)
# REDIS_URL=redis://localhost:6379/0
```

---

## Next Steps

After verifying all security features work:

1. ✅ All three security features tested and working
2. Update production CORS domains in `config.py`
3. Implement Redis-based rate limiting for production
4. Set up monitoring and alerting (Sentry, Datadog, etc.)
5. Perform security audit with OWASP ZAP or similar
6. Deploy to staging environment
7. Run full security test suite in staging
8. Deploy to production

---

## Security Checklist

Before deploying to production:

- [ ] RLS migration run on production database
- [ ] All RLS policies tested (logged-in, no auth, insert attack)
- [ ] Rate limiting tested for all tiers (Free, Pro, Enterprise)
- [ ] Production CORS domains configured (no placeholders!)
- [ ] `ENVIRONMENT=production` set in production `.env`
- [ ] SSL enforcement enabled in Supabase
- [ ] Service role key secured (never exposed to frontend)
- [ ] Redis-based rate limiter implemented
- [ ] Monitoring and alerting configured
- [ ] Security audit completed
- [ ] Incident response plan documented
- [ ] Team trained on security features

---

## Getting Help

If you encounter issues:

1. Check the logs: `tail -f backend/logs/app.log`
2. Review SECURITY_IMPLEMENTATION_GUIDE.md for detailed explanations
3. Check Supabase Dashboard > Logs for RLS policy violations
4. Use browser DevTools > Network to debug CORS issues
5. Test with curl/Postman to isolate frontend vs backend issues

**Remember:**
- RLS is enforced at database level - even service role sees all data
- Rate limiting is per-user, not per-IP
- CORS only affects browser requests, not server-to-server

Your security foundation is solid! 🔐
