# AI WebScraper - Architecture & Monetization Plan

## Overview

This document outlines the remaining architecture components needed to transform the AI WebScraper into a production-ready SaaS platform with OAuth authentication, robust state management, comprehensive error handling, and a clear monetization strategy.

---

## 1. Authentication & Security Architecture

### 1.1 OAuth Integration (Google & GitHub)

**Current State:**

- Basic Supabase authentication with email/password
- JWT token verification in place
- Row Level Security (RLS) configured

**Required Implementation:**

#### **Google OAuth**

- **Provider Setup:**
  - Create Google Cloud Console project
  - Configure OAuth 2.0 credentials
  - Set authorized redirect URIs
  - Add to Supabase Auth providers
- **Scopes Required:**
  - `openid`
  - `email`
  - `profile`
- **User Flow:**
  1. User clicks "Sign in with Google"
  2. Redirect to Google consent screen
  3. Google redirects back with authorization code
  4. Supabase exchanges code for tokens
  5. User profile created/updated in database
  6. JWT issued for session management

#### **GitHub OAuth**

- **Provider Setup:**
  - Create GitHub OAuth App
  - Configure callback URL
  - Add to Supabase Auth providers
- **Scopes Required:**
  - `user:email`
  - `read:user`
- **User Flow:**
  1. User clicks "Sign in with GitHub"
  2. Redirect to GitHub authorization
  3. GitHub redirects back with code
  4. Supabase handles token exchange
  5. User profile synced to database

#### **Implementation Files:**

```
frontend/src/
  ├── components/
  │   ├── AuthProvider.tsx          # OAuth context provider
  │   ├── GoogleSignInButton.tsx    # Google OAuth button
  │   └── GitHubSignInButton.tsx    # GitHub OAuth button
  ├── pages/
  │   ├── LoginPage.tsx              # Updated with OAuth options
  │   └── CallbackPage.tsx           # OAuth callback handler
  └── hooks/
      └── useAuth.tsx                # Authentication hook

backend/app/
  ├── core/
  │   └── oauth.py                   # OAuth configuration
  └── api/routes/
      └── auth.py                    # OAuth endpoints
```

### 1.2 Enhanced Security Features

#### **Session Management**

- **Access Tokens:** Short-lived (1 hour)
- **Refresh Tokens:** Long-lived (30 days)
- **Token Rotation:** Automatic refresh before expiry
- **Secure Storage:** HttpOnly cookies for tokens

#### **Row Level Security (RLS) Policies**

```sql
-- Users can only see their own data
CREATE POLICY "Users can view own crawls"
  ON crawls FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own crawls"
  ON crawls FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own crawls"
  ON crawls FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own crawls"
  ON crawls FOR DELETE
  USING (auth.uid() = user_id);

-- Cascade to all related tables (pages, links, images, issues)
```

#### **API Security**

- **Rate Limiting:**
  - Free tier: 10 requests/minute
  - Pro tier: 100 requests/minute
  - Enterprise: Unlimited
- **CORS Configuration:**
  - Whitelist production domains
  - Restrict methods (GET, POST, PATCH, DELETE)
- **Input Validation:**
  - Pydantic models for all endpoints
  - SQL injection prevention
  - XSS protection

#### **Data Privacy**

- **GDPR Compliance:**
  - User data export endpoint
  - Account deletion with cascade
  - Privacy policy page
  - Cookie consent banner
- **Encryption:**
  - TLS 1.3 for all connections
  - Encrypted environment variables
  - Secure password hashing (bcrypt)

---

## 2. State Management Architecture

### 2.1 Current State (Problems)

**Issues:**

- Multiple `useState` hooks scattered across components
- Props drilling for shared state
- No centralized auth state
- Difficult to debug state changes
- No persistence across page refreshes

### 2.2 Recommended Solution: Zustand

**Why Zustand over Redux/Context:**

- ✅ Minimal boilerplate
- ✅ TypeScript-first
- ✅ Easy to learn
- ✅ Excellent performance
- ✅ Built-in persistence
- ✅ DevTools support

#### **Store Structure**

```typescript
// stores/authStore.ts
interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signInWithGitHub: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

// stores/crawlStore.ts
interface CrawlState {
  crawls: Crawl[];
  activeCrawl: Crawl | null;
  isLoading: boolean;
  fetchCrawls: () => Promise<void>;
  createCrawl: (data: CreateCrawlData) => Promise<void>;
  deleteCrawl: (id: string) => Promise<void>;
  rerunCrawl: (id: string) => Promise<void>;
}

// stores/uiStore.ts
interface UIState {
  sidebarOpen: boolean;
  theme: "light" | "dark";
  notifications: Notification[];
  toggleSidebar: () => void;
  setTheme: (theme: "light" | "dark") => void;
  addNotification: (notification: Notification) => void;
}

// stores/subscriptionStore.ts
interface SubscriptionState {
  tier: "free" | "pro" | "enterprise";
  usage: UsageMetrics;
  limits: TierLimits;
  fetchSubscription: () => Promise<void>;
  upgradeTier: (tier: string) => Promise<void>;
}
```

#### **Implementation Files:**

```
frontend/src/
  ├── stores/
  │   ├── authStore.ts           # Authentication state
  │   ├── crawlStore.ts          # Crawl management state
  │   ├── uiStore.ts             # UI preferences state
  │   └── subscriptionStore.ts   # Subscription & billing state
  ├── hooks/
  │   ├── useAuth.ts             # Auth store hook
  │   ├── useCrawls.ts           # Crawl store hook
  │   └── useSubscription.ts     # Subscription hook
  └── middleware/
      └── persistence.ts         # LocalStorage persistence
```

### 2.3 State Persistence

**LocalStorage Strategy:**

- **Persist:** User preferences, theme, sidebar state
- **Session Storage:** Active filters, sort preferences
- **Do NOT Persist:** Sensitive data (tokens stored in HttpOnly cookies)

---

## 3. Error Handling & Monitoring

### 3.1 Frontend Error Handling

#### **Error Boundary Component**

```typescript
// components/ErrorBoundary.tsx
- Catch React component errors
- Display fallback UI
- Log errors to monitoring service
- Provide "Retry" and "Report" actions
```

#### **API Error Handling**

```typescript
// services/api.ts
- Centralized error interceptor
- Automatic retry for 5xx errors (3 attempts)
- User-friendly error messages
- Toast notifications for errors
- Redirect to login on 401
```

#### **Error Types & Messages**

```typescript
enum ErrorType {
  NETWORK_ERROR = "Unable to connect. Check your internet.",
  AUTH_ERROR = "Session expired. Please sign in again.",
  VALIDATION_ERROR = "Invalid input. Please check your data.",
  RATE_LIMIT = "Too many requests. Please wait.",
  SERVER_ERROR = "Server error. We're working on it.",
  NOT_FOUND = "Resource not found.",
  PERMISSION_DENIED = "You don't have permission for this action.",
}
```

### 3.2 Backend Error Handling

#### **Custom Exception Classes**

```python
# app/core/exceptions.py
class CrawlNotFoundException(HTTPException)
class InsufficientCreditsException(HTTPException)
class RateLimitExceededException(HTTPException)
class InvalidCrawlConfigException(HTTPException)
```

#### **Global Exception Handler**

```python
# app/main.py
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    - Log error with context
    - Return standardized error response
    - Send to monitoring service
```

### 3.3 Monitoring & Logging

#### **Recommended Tools**

**Option 1: Sentry (Recommended)**

- Real-time error tracking
- Performance monitoring
- User session replay
- Release tracking
- Free tier: 5,000 events/month

**Option 2: LogRocket**

- Session replay
- Error tracking
- Performance monitoring
- User analytics

**Option 3: Self-Hosted (Budget Option)**

- **Frontend:** Custom error logger → Supabase table
- **Backend:** Python logging → File/Database
- **Monitoring:** Uptime Robot (free)

#### **Implementation:**

```
frontend/src/
  └── services/
      └── monitoring.ts          # Sentry/LogRocket integration

backend/app/
  ├── core/
  │   └── logging.py             # Structured logging
  └── middleware/
      └── error_tracking.py      # Error monitoring
```

#### **Metrics to Track**

- **Performance:**
  - API response times
  - Page load times
  - Crawl completion times
- **Errors:**
  - Error rate by endpoint
  - Failed crawls by reason
  - Authentication failures
- **Business:**
  - Daily active users
  - Crawls per user
  - Conversion rate (free → paid)
  - Churn rate

---

## 4. Monetization Strategy

### 4.1 Pricing Tiers

#### **Free Tier (Freemium)**

**Purpose:** User acquisition, product validation

**Limits:**

- 5 crawls per month
- 50 pages per crawl
- 1 concurrent crawl
- Basic issue detection (9 categories)
- 7-day data retention
- Community support

**Features:**

- ✅ OAuth sign-in (Google/GitHub)
- ✅ Basic SEO analysis
- ✅ Link & image extraction
- ✅ CSV export
- ✅ Search & filtering
- ❌ No AI-powered insights
- ❌ No API access
- ❌ No white-label reports

**Target:** Small businesses, freelancers, students

---

#### **Pro Tier - $29/month**

**Purpose:** Primary revenue driver, power users

**Limits:**

- 100 crawls per month
- 1,000 pages per crawl
- 5 concurrent crawls
- Advanced issue detection (20+ categories)
- 90-day data retention
- Email support (24-hour response)

**Features:**

- ✅ Everything in Free
- ✅ **AI-Powered Content Audits** (GPT-4)
  - Readability analysis
  - Keyword density
  - Content quality scoring
  - Duplicate content detection
- ✅ **Advanced SEO Analysis**
  - Schema markup detection
  - Open Graph validation
  - Canonical tag analysis
- ✅ **Scheduled Crawls** (weekly/monthly)
- ✅ **Email Notifications**
- ✅ **PDF Reports** (branded)
- ✅ **Priority Processing**
- ✅ **API Access** (1,000 requests/day)

**Target:** Marketing agencies, SEO consultants, growing businesses

---

#### **Enterprise Tier - Custom Pricing**

**Purpose:** High-value clients, custom solutions

**Limits:**

- Unlimited crawls
- Unlimited pages per crawl
- Unlimited concurrent crawls
- Custom issue detection rules
- Unlimited data retention
- Dedicated account manager
- SLA guarantee (99.9% uptime)

**Features:**

- ✅ Everything in Pro
- ✅ **White-Label Reports** (custom branding)
- ✅ **Custom Integrations** (Slack, Teams, webhooks)
- ✅ **Multi-User Accounts** (team management)
- ✅ **SSO Integration** (SAML)
- ✅ **Custom AI Models** (fine-tuned for industry)
- ✅ **Dedicated Infrastructure**
- ✅ **API Access** (unlimited)
- ✅ **Custom Crawl Rules**
- ✅ **Priority Support** (phone, Slack)

**Target:** Large enterprises, agencies with 10+ clients

---

### 4.2 Upsell Strategy

#### **In-App Upsell Triggers**

**1. Usage Limits Reached**

```
┌─────────────────────────────────────────────┐
│  🚀 You've reached your crawl limit!        │
│                                             │
│  Free: 5/5 crawls used this month          │
│                                             │
│  Upgrade to Pro for:                        │
│  ✓ 100 crawls/month                        │
│  ✓ AI-powered insights                     │
│  ✓ Scheduled crawls                        │
│                                             │
│  [Upgrade to Pro - $29/mo] [Maybe Later]   │
└─────────────────────────────────────────────┘
```

**2. Feature Gating**

- **AI Content Audit:** Show preview, require Pro
- **Scheduled Crawls:** "Pro Feature" badge
- **PDF Reports:** Generate sample, watermark "Upgrade to Pro"
- **API Access:** Show documentation, require Pro

**3. Value Demonstration**

- **Dashboard Widget:** "You've found 247 issues! Upgrade to get AI-powered fix suggestions."
- **Issue Detail:** "Pro users get detailed fix guides for this issue."
- **Export Limit:** "Free users can export 100 rows. Upgrade for unlimited exports."

#### **Conversion Funnel**

```
Free Signup
    ↓
First Crawl (within 24 hours)
    ↓
3+ Crawls (engaged user)
    ↓
Hit Limit (upsell moment)
    ↓
Trial Offer (14-day Pro trial)
    ↓
Convert to Pro
```

#### **Retention Tactics**

**For Free Users:**

- Monthly email: "Your crawl summary + Pro features you're missing"
- In-app tips: "Did you know Pro users can schedule crawls?"
- Limited-time offers: "Get 20% off Pro - First month only"

**For Pro Users:**

- Usage reports: "You saved 15 hours this month with scheduled crawls"
- Feature announcements: Early access to new features
- Referral program: "Refer 3 clients, get 1 month free"

**For Enterprise:**

- Quarterly business reviews
- Custom feature development
- Dedicated Slack channel

---

### 4.3 Payment Integration

#### **Recommended: Stripe**

**Why Stripe:**

- ✅ Supabase integration available
- ✅ Subscription management built-in
- ✅ Automatic invoicing
- ✅ Tax calculation
- ✅ Multiple payment methods
- ✅ Dunning management (failed payments)

#### **Implementation:**

```
frontend/src/
  ├── pages/
  │   ├── PricingPage.tsx        # Pricing tiers display
  │   ├── CheckoutPage.tsx       # Stripe checkout
  │   └── BillingPage.tsx        # Manage subscription
  └── components/
      ├── PricingCard.tsx        # Tier comparison
      └── UpgradeModal.tsx       # Upsell modal

backend/app/
  ├── services/
  │   ├── stripe_service.py      # Stripe API wrapper
  │   └── subscription.py        # Subscription logic
  └── api/routes/
      ├── billing.py             # Billing endpoints
      └── webhooks.py            # Stripe webhooks
```

#### **Database Schema:**

```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  tier TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')),
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing')),
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE usage_tracking (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  month DATE NOT NULL,
  crawls_used INTEGER DEFAULT 0,
  pages_crawled INTEGER DEFAULT 0,
  api_requests INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE tier_limits (
  tier TEXT PRIMARY KEY,
  crawls_per_month INTEGER NOT NULL,
  max_pages_per_crawl INTEGER NOT NULL,
  concurrent_crawls INTEGER NOT NULL,
  data_retention_days INTEGER NOT NULL,
  api_requests_per_day INTEGER NOT NULL,
  features JSONB NOT NULL
);
```

---

### 4.4 Usage Tracking & Enforcement

#### **Middleware Implementation:**

```python
# app/middleware/usage_limiter.py

async def check_crawl_limit(user_id: str, tier: str):
    """Check if user can start a new crawl."""
    current_month = datetime.now().replace(day=1)
    usage = get_usage(user_id, current_month)
    limits = get_tier_limits(tier)

    if usage.crawls_used >= limits.crawls_per_month:
        raise InsufficientCreditsException(
            "Monthly crawl limit reached. Upgrade to Pro for more crawls."
        )

    return True

async def check_concurrent_limit(user_id: str, tier: str):
    """Check if user can run concurrent crawls."""
    active_crawls = count_active_crawls(user_id)
    limits = get_tier_limits(tier)

    if active_crawls >= limits.concurrent_crawls:
        raise RateLimitExceededException(
            f"Maximum {limits.concurrent_crawls} concurrent crawls allowed."
        )

    return True
```

#### **Frontend Usage Display:**

```typescript
// components/UsageWidget.tsx
<div className="usage-widget">
  <h3>Your Usage This Month</h3>
  <ProgressBar
    current={usage.crawls_used}
    max={limits.crawls_per_month}
    label="Crawls"
  />
  <ProgressBar
    current={usage.pages_crawled}
    max={limits.max_pages_per_crawl * limits.crawls_per_month}
    label="Pages"
  />
  {usage.crawls_used / limits.crawls_per_month > 0.8 && (
    <Alert variant="warning">
      You've used 80% of your monthly crawls.
      <Link to="/pricing">Upgrade to Pro</Link>
    </Alert>
  )}
</div>
```

---

## 5. Implementation Roadmap

### **Phase 1: Authentication & Security (Week 1-2)**

- [ ] Set up Google OAuth in Supabase
- [ ] Set up GitHub OAuth in Supabase
- [ ] Create OAuth sign-in buttons
- [ ] Implement OAuth callback handling
- [ ] Update RLS policies for multi-user
- [ ] Add session management
- [ ] Implement token refresh logic
- [ ] Add GDPR compliance pages (Privacy Policy, Terms)

### **Phase 2: State Management (Week 2-3)**

- [ ] Install and configure Zustand
- [ ] Create auth store
- [ ] Create crawl store
- [ ] Create UI store
- [ ] Create subscription store
- [ ] Migrate existing useState to stores
- [ ] Add persistence middleware
- [ ] Test state across page refreshes

### **Phase 3: Error Handling & Monitoring (Week 3-4)**

- [ ] Set up Sentry account
- [ ] Integrate Sentry in frontend
- [ ] Integrate Sentry in backend
- [ ] Create ErrorBoundary component
- [ ] Implement API error interceptor
- [ ] Add structured logging to backend
- [ ] Set up performance monitoring
- [ ] Create error tracking dashboard

### **Phase 4: Subscription & Billing (Week 4-6)**

- [ ] Create Stripe account
- [ ] Set up Stripe products (Free, Pro, Enterprise)
- [ ] Implement Stripe checkout flow
- [ ] Create billing page
- [ ] Implement subscription webhooks
- [ ] Add usage tracking
- [ ] Implement tier limits enforcement
- [ ] Create pricing page
- [ ] Add upgrade modals
- [ ] Test payment flow end-to-end

### **Phase 5: Upsell & Retention (Week 6-7)**

- [ ] Implement usage limit warnings
- [ ] Create upgrade CTAs
- [ ] Add feature gating
- [ ] Implement trial offers
- [ ] Create email notification system
- [ ] Add referral program
- [ ] Build admin dashboard for monitoring

### **Phase 6: Testing & Launch (Week 7-8)**

- [ ] End-to-end testing
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation
- [ ] Beta user testing
- [ ] Production deployment
- [ ] Marketing launch

---

## 6. Cost Analysis

### **Monthly Operating Costs (Estimated)**

| Service              | Free Tier      | Pro Tier (100 users) | Enterprise (10 clients) |
| -------------------- | -------------- | -------------------- | ----------------------- |
| **Supabase**         | $0             | $25/mo               | $599/mo                 |
| **Stripe**           | 2.9% + $0.30   | ~$100/mo fees        | ~$500/mo fees           |
| **Sentry**           | $0 (5k events) | $26/mo               | $80/mo                  |
| **OpenAI API**       | N/A            | $200/mo              | $1,000/mo               |
| **Hosting (Vercel)** | $0             | $20/mo               | $20/mo                  |
| **Domain & SSL**     | $12/year       | $12/year             | $12/year                |
| **Email (SendGrid)** | $0 (100/day)   | $15/mo               | $15/mo                  |
| **Total**            | **~$1/mo**     | **~$386/mo**         | **~$2,214/mo**          |

### **Revenue Projections**

**Conservative (Year 1):**

- 1,000 free users
- 50 Pro users ($29/mo) = **$1,450/mo**
- 2 Enterprise clients ($500/mo) = **$1,000/mo**
- **Total: $2,450/mo** ($29,400/year)
- **Profit: ~$2,000/mo** after costs

**Optimistic (Year 2):**

- 10,000 free users
- 500 Pro users = **$14,500/mo**
- 20 Enterprise clients = **$10,000/mo**
- **Total: $24,500/mo** ($294,000/year)
- **Profit: ~$22,000/mo** after costs

---

## 7. Success Metrics

### **Product Metrics**

- **Activation Rate:** % of signups who complete first crawl (Target: 60%)
- **Engagement:** Average crawls per active user (Target: 3/month)
- **Retention:** % of users active after 30 days (Target: 40%)

### **Business Metrics**

- **Conversion Rate:** Free → Pro (Target: 5%)
- **MRR Growth:** Month-over-month (Target: 20%)
- **Churn Rate:** Monthly (Target: <5%)
- **LTV:CAC Ratio:** Lifetime value / Customer acquisition cost (Target: 3:1)

### **Technical Metrics**

- **Uptime:** (Target: 99.9%)
- **API Response Time:** (Target: <500ms p95)
- **Crawl Success Rate:** (Target: >95%)
- **Error Rate:** (Target: <1%)

---

## Summary

This architecture plan provides a complete roadmap for transforming the AI WebScraper into a production-ready SaaS platform with:

1. ✅ **OAuth Authentication** - Google & GitHub sign-in
2. ✅ **Robust State Management** - Zustand for predictable state
3. ✅ **Comprehensive Error Handling** - Sentry monitoring
4. ✅ **Clear Monetization Strategy** - Free/Pro/Enterprise tiers
5. ✅ **Usage Tracking & Enforcement** - Tier-based limits
6. ✅ **Payment Processing** - Stripe integration
7. ✅ **Upsell Mechanisms** - In-app conversion funnels

**Estimated Timeline:** 8 weeks for full implementation
**Estimated Cost:** $400-2,200/month operating costs
**Revenue Potential:** $2,500-25,000/month within first year
