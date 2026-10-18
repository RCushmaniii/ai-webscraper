# Security Implementation Guide

## Overview

This guide covers the three critical security features implemented in Weeks 1-2:

1. **RLS Enhancement Migration** - Bulletproof row-level security policies
2. **Rate Limiting Middleware** - Prevent API abuse by tier (Free, Pro, Enterprise)
3. **CORS Configuration** - Lock down production domains

---

## 1. Row-Level Security (RLS) Enhancement

### What is RLS?

Row-Level Security is PostgreSQL's database-level security mechanism that restricts which rows a user can access. It's enforced at the database level, making it impossible to bypass from the application layer.

### Why Both USING and WITH CHECK?

This is the most critical RLS concept:

- **USING clause**: Controls which rows the user can READ (SELECT)
- **WITH CHECK clause**: Controls which rows the user can WRITE (INSERT/UPDATE)

**Example Problem Without WITH CHECK:**

```sql
-- ❌ INSECURE - Only has USING clause
CREATE POLICY "crawls_update_own"
  ON crawls FOR UPDATE
  USING (auth.uid() = user_id);
  -- Missing WITH CHECK!

-- Attack: User can transfer ownership to someone else!
UPDATE crawls SET user_id = 'attacker-id' WHERE id = 'my-crawl-id';
-- This succeeds because USING only checks the OLD row!
```

**Secure Version With Both Clauses:**

```sql
-- ✅ SECURE - Has both USING and WITH CHECK
CREATE POLICY "crawls_update_own"
  ON crawls FOR UPDATE
  USING (auth.uid() = user_id)         -- Can only update OWN crawls
  WITH CHECK (auth.uid() = user_id);   -- Cannot change user_id to someone else
```

### Migration File

**Location:** `database/migrations/004_enhance_rls_policies.sql`

This migration:
- ✅ Enables RLS on all user data tables
- ✅ Drops old insecure policies
- ✅ Creates new policies with both USING and WITH CHECK
- ✅ Uses EXISTS subqueries for related tables (pages, links, images, etc.)
- ✅ Includes verification function

### Tables Covered

| Table | SELECT | INSERT | UPDATE | DELETE |
|-------|--------|--------|--------|--------|
| users | ✅ Own | ✅ Own | ✅ Own | ✅ Own |
| crawls | ✅ Own | ✅ Own | ✅ Own | ✅ Own |
| pages | ✅ Via crawl | Service role only | Service role only | Service role only |
| links | ✅ Via crawl | Service role only | Service role only | Service role only |
| images | ✅ Via crawl | Service role only | Service role only | Service role only |
| seo_metadata | ✅ Via page | Service role only | Service role only | Service role only |
| issues | ✅ Via crawl | Service role only | Service role only | Service role only |
| summaries | ✅ Via crawl | Service role only | Service role only | Service role only |

### Key RLS Principles

**1. NEVER trust frontend checks**
```javascript
// ❌ INSECURE - Trusting frontend to send correct user_id
const { data } = await supabase
  .from('crawls')
  .insert({ user_id: currentUser.id, url: '...' });
// Attacker can modify currentUser.id in browser!

// ✅ SECURE - RLS WITH CHECK clause enforces user_id = auth.uid()
CREATE POLICY "crawls_insert_own"
  ON crawls FOR INSERT
  WITH CHECK (auth.uid() = user_id);
// Even if attacker sends wrong user_id, database rejects it!
```

**2. Service role bypasses RLS (backend only)**
```python
# Backend using service role key - bypasses RLS
from app.db.supabase import supabase_service_role

# This can insert pages even though users can't directly modify pages
await supabase_service_role.table("pages").insert({
    "crawl_id": crawl_id,
    "url": url,
    "content": content
})
# This is SAFE because it's backend-only (users never get service role key)
```

**3. Test all three scenarios**
- ✅ Logged-in user can access own data
- ✅ Logged-in user CANNOT access other users' data
- ✅ Unauthenticated user CANNOT access any data
- ✅ Insert attack (trying to set user_id to someone else) FAILS

### Testing RLS Policies

**Run the migration:**
```bash
# Connect to Supabase and run the migration
psql "postgresql://postgres:[YOUR-PASSWORD]@db.your-project.supabase.co:5432/postgres" -f database/migrations/004_enhance_rls_policies.sql
```

**Or via Supabase Dashboard:**
1. Go to SQL Editor
2. Copy contents of `004_enhance_rls_policies.sql`
3. Run the migration
4. Check output of `test_rls_policies()` function

**Test 1: Verify RLS is enabled**
```sql
SELECT * FROM test_rls_policies();
-- Should show all tables have RLS enabled
```

**Test 2: Try to access another user's data**
```sql
-- As logged-in user
SELECT * FROM crawls WHERE user_id != auth.uid();
-- Should return 0 rows (even if other users' crawls exist)
```

**Test 3: Try insert attack**
```sql
-- Try to create a crawl for someone else
INSERT INTO crawls (user_id, url, name, status)
VALUES ('some-other-user-id', 'https://example.com', 'Test', 'pending');
-- Should FAIL with: new row violates row-level security policy
```

---

## 2. Rate Limiting Middleware

### Subscription Tiers

Our freemium business model has three tiers:

| Feature | Free (Free) | Pro ($29/month) | Enterprise (Custom) |
|---------|-------------|-----------------|---------------------|
| Requests/minute | 10 | 60 | 300 |
| Requests/hour | 100 | 1,000 | 10,000 |
| Requests/day | 500 | 10,000 | 100,000 |
| Crawls/month | 5 | 100 | Unlimited |
| Pages/crawl | 50 | 1,000 | 10,000 |
| Concurrent crawls | 1 | 3 | 10 |
| API requests/day | 100 | 1,000 | 100,000 |

### Implementation Files

**Configuration:** `backend/app/core/rate_limits.py`
- Defines `RateLimit` dataclass
- `RATE_LIMITS` dictionary with tier configurations
- Helper functions: `get_rate_limit()`, `get_tier_from_user()`, `get_upgrade_message()`

**Middleware:** `backend/app/middleware/rate_limiter.py`
- `InMemoryRateLimiter` class for development
- `RedisRateLimiter` class (TODO for production)
- `rate_limit_middleware()` - FastAPI middleware function
- `@rate_limit()` decorator for route-specific limits

### How Rate Limiting Works

**1. In-Memory Limiter (Development)**

```python
# Tracks requests in memory (not suitable for multi-worker production)
class InMemoryRateLimiter:
    def __init__(self):
        self.storage: Dict[str, Dict[str, any]] = {}
        # Key format: "user:{user_id}:{limit_type}"
        # Value: {"count": 5, "reset_time": 1641234567}
```

**Warning:** In-memory storage is lost when server restarts and doesn't work across multiple workers!

**2. Redis Limiter (Production - TODO)**

For production, use Redis for distributed rate limiting:

```python
# TODO: Implement RedisRateLimiter
# Benefits:
# - Survives server restarts
# - Works across multiple workers/servers
# - Atomic increment operations
# - Built-in expiration (TTL)
```

### Middleware Integration

**Added to `backend/app/main.py`:**

```python
from app.middleware.rate_limiter import rate_limit_middleware

# Middleware order matters!
# 1. CORS (must be first for preflight)
# 2. Rate limiting (check limits early)
# 3. Request logging (log everything)

app.middleware("http")(rate_limit_middleware)
```

### Rate Limit Response

When a user exceeds their limit:

```json
{
  "detail": "Rate limit exceeded: Too many requests per minute. Please slow down. Upgrade to Pro ($29/month) for much higher limits.",
  "retry_after": 60,
  "upgrade_url": "/pricing"
}
```

HTTP Status: `429 Too Many Requests`

Headers:
```
Retry-After: 60
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
```

### Route-Specific Rate Limiting

You can apply stricter limits to expensive endpoints:

```python
from app.middleware.rate_limiter import rate_limit

@router.post("/crawls")
@rate_limit("rph")  # Check hourly limit instead of per-minute
async def create_crawl(request: Request, crawl_data: CrawlCreate):
    # Only allow X crawls per hour based on tier
    pass
```

### Usage Tracking (TODO)

For monthly limits (crawls_per_month), we need usage tracking:

```python
# TODO: Implement when adding subscriptions
def check_monthly_crawl_limit(user_id: str, tier: str) -> Tuple[bool, str]:
    """
    Query database for current month's crawl count.
    Compare against tier limit.
    """
    # Query: SELECT COUNT(*) FROM crawls
    #        WHERE user_id = ? AND created_at >= date_trunc('month', now())
    pass
```

---

## 3. CORS Configuration

### What is CORS?

Cross-Origin Resource Sharing (CORS) is a security feature that restricts which domains can access your API.

**Without CORS:** Anyone can call your API from any website
**With CORS:** Only approved domains can call your API

### Environment-Based Configuration

**Development (permissive):**
```python
# Allow all localhost ports for local development
_DEV_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",  # Vite
    "http://127.0.0.1:3000",
]
```

**Production (strict):**
```python
# ONLY your actual production domains
_PROD_CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://app.yourdomain.com",
]
```

**Staging:**
```python
# Staging domains + dev (for testing)
_STAGING_CORS_ORIGINS = [
    "https://staging.yourdomain.com",
    "https://dev.yourdomain.com",
] + _DEV_CORS_ORIGINS
```

### Configuration Priority

The `BACKEND_CORS_ORIGINS` property uses this priority:

1. **Environment variable** `CORS_ORIGINS` (comma-separated)
2. **Environment-specific defaults** based on `ENVIRONMENT` variable

**Example `.env` configurations:**

```bash
# Development (default)
ENVIRONMENT=development
# Uses _DEV_CORS_ORIGINS automatically

# Production
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
# Or omit CORS_ORIGINS to use _PROD_CORS_ORIGINS defaults
```

### CORS Security Best Practices

**DO:**
- ✅ Use specific domains in production
- ✅ Use HTTPS in production (never HTTP)
- ✅ Set `allow_credentials=True` for auth cookies
- ✅ Limit `allow_methods` to only what you need
- ✅ Test CORS in staging before production

**DON'T:**
- ❌ NEVER use `"*"` wildcard in production
- ❌ Don't allow HTTP in production (only HTTPS)
- ❌ Don't hardcode production domains in code (use env vars)
- ❌ Don't include test/dev domains in production

### Testing CORS

**Test 1: Development CORS**
```bash
# Start frontend on localhost:3000
npm run dev

# Make API call - should work
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8000/api/v1/crawls
# Should return: Access-Control-Allow-Origin: http://localhost:3000
```

**Test 2: Production CORS**
```bash
# Set environment
export ENVIRONMENT=production
export CORS_ORIGINS=https://yourdomain.com

# Start backend
uvicorn app.main:app

# Test allowed origin
curl -H "Origin: https://yourdomain.com" \
     -X OPTIONS https://api.yourdomain.com/api/v1/crawls
# Should succeed

# Test blocked origin
curl -H "Origin: https://evil.com" \
     -X OPTIONS https://api.yourdomain.com/api/v1/crawls
# Should fail (no Access-Control-Allow-Origin header)
```

**Test 3: Browser DevTools**
```javascript
// In browser console on your frontend domain
fetch('https://api.yourdomain.com/api/v1/crawls', {
  credentials: 'include'
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
// Should work from approved domain
// Should fail with CORS error from other domains
```

---

## Deployment Checklist

### Development Environment

- [x] RLS migration created
- [x] Rate limiting middleware implemented
- [x] CORS configuration set up
- [ ] Run RLS migration in local Supabase
- [ ] Test rate limiting with Postman/curl
- [ ] Test CORS from frontend
- [ ] Verify all security features work together

### Staging Environment

- [ ] Set `ENVIRONMENT=staging` in `.env`
- [ ] Run RLS migration on staging database
- [ ] Configure staging CORS origins
- [ ] Test user authentication flow
- [ ] Test rate limiting with different tiers
- [ ] Verify RLS policies prevent data leakage
- [ ] Load test rate limiting

### Production Environment

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configure production CORS origins (comma-separated list)
- [ ] Run RLS migration on production database
- [ ] **CRITICAL:** Replace placeholder domains in `_PROD_CORS_ORIGINS`
- [ ] Implement Redis-based rate limiter (replace in-memory)
- [ ] Set up database usage tracking table
- [ ] Configure monitoring and alerts
- [ ] Test all security features end-to-end
- [ ] Perform security audit
- [ ] Document incident response procedures

---

## Monitoring & Alerts

### What to Monitor

**1. Rate Limiting**
- Rate limit hits per tier (Free, Pro, Enterprise)
- Users hitting limits frequently (may need upgrade prompts)
- Unusual spike in requests (potential attack)
- In-memory storage size (memory leak detection)

**2. RLS Policies**
- Policy violations (failed SELECT/INSERT/UPDATE attempts)
- Service role usage (should only be backend)
- Unauthorized access attempts
- Performance impact of complex EXISTS queries

**3. CORS**
- Blocked CORS requests (may indicate misconfiguration)
- Requests from unexpected origins (potential attack)
- Failed preflight requests
- Production CORS misconfiguration

### Suggested Alerts

```python
# Example monitoring setup
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Alert when user hits rate limit multiple times
def alert_frequent_rate_limit_hits(user_id: str, count: int):
    if count > 5:  # 5 times in 1 hour
        logger.warning(f"User {user_id} hit rate limit {count} times - may need upgrade")

# Alert on RLS policy violations
def alert_rls_violation(user_id: str, table: str, operation: str):
    logger.error(f"RLS violation: User {user_id} attempted {operation} on {table}")

# Alert on CORS from unexpected origin
def alert_cors_violation(origin: str, ip: str):
    logger.warning(f"CORS blocked: {origin} from IP {ip}")
```

### Recommended Monitoring Tools

- **Sentry** - Error tracking and performance monitoring
- **Datadog** - Infrastructure and APM
- **CloudWatch** (AWS) - Logs and metrics
- **Supabase Dashboard** - Database queries and RLS policy hits
- **Grafana + Prometheus** - Custom metrics and dashboards

---

## Security Incident Response

### If RLS Policy is Bypassed

1. **Immediately:** Revoke compromised service role key
2. Review all database audit logs
3. Identify affected users and data
4. Patch the vulnerability
5. Run security audit
6. Notify affected users (GDPR compliance)
7. Post-mortem and improve policies

### If Rate Limit is Bypassed

1. Block IP addresses if attack is ongoing
2. Implement additional rate limiting (IP-based)
3. Review attack patterns
4. Implement Redis-based limiter if using in-memory
5. Add CAPTCHA for suspicious patterns
6. Update rate limit logic

### If CORS is Misconfigured

1. Immediately fix CORS configuration
2. Review recent API access logs
3. Identify unauthorized origins
4. Check for data leakage
5. Update security documentation
6. Add automated CORS testing

---

## Next Steps (Weeks 2-3)

After completing security foundations, the next tasks are:

1. **Zustand State Management**
   - Install Zustand and Zustand persist
   - Create `authMirrorStore` (memory only - never persisted)
   - Create `uiStore` (persisted - safe UI state)
   - Create `selectionStore` (memory only - volatile)
   - Migrate from Context to Zustand

2. **Subscription Integration**
   - Add Stripe integration
   - Create subscriptions table
   - Implement `get_tier_from_user()` with real database query
   - Add usage tracking table
   - Implement monthly crawl limit checking
   - Create upgrade flow

3. **Redis Rate Limiting**
   - Set up Redis instance
   - Implement `RedisRateLimiter` class
   - Test distributed rate limiting
   - Deploy to production

---

## Resources

### Documentation
- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [CORS Explained](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

### Security Best Practices
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Supabase Security Best Practices](https://supabase.com/docs/guides/platform/going-into-prod#security)

### Testing Tools
- [Postman](https://www.postman.com/) - API testing
- [curl](https://curl.se/) - Command-line API testing
- [OWASP ZAP](https://www.zaproxy.org/) - Security testing
- [pgTAP](https://pgtap.org/) - PostgreSQL unit testing

---

## Summary

You've now implemented three critical security features:

1. ✅ **RLS Enhancement** - Database-level security with both USING and WITH CHECK clauses
2. ✅ **Rate Limiting** - Tier-based API protection (Free/Pro/Enterprise)
3. ✅ **CORS Configuration** - Environment-specific domain restrictions

**Next Steps:**
1. Run the RLS migration in your Supabase database
2. Test all three security features in development
3. Update production CORS domains before deploying
4. Implement Redis-based rate limiting for production

**Remember:**
- NEVER trust frontend checks - RLS enforces at database level
- Service role key bypasses RLS - backend only!
- Test all three scenarios: logged-in, no auth, insert attack
- NEVER use CORS wildcard in production
- Monitor and alert on security violations

Your application is now significantly more secure! 🔐
