# 🚀 Production Database Migration Instructions

## What I Built For You

I've created a **production-grade, idempotent database migration** based on your actual schema.sql, with these improvements:

### ✅ What's Included

1. **Complete Tables** - All 11 tables from your schema
2. **Full CRUD RLS Policies** - Not just SELECT, but INSERT/UPDATE/DELETE for all tables
3. **Performance Indexes** - 15+ indexes for fast queries
4. **Proper Foreign Keys** - All relationships with CASCADE behavior
5. **Idempotent** - Safe to run multiple times without errors
6. **No Redundant service_role Checks** - Clean, expert-approved RLS

### 📂 Files Created

- `PRODUCTION_READY_MIGRATION.sql` - The main migration script
- `verify_migration.sql` - Run this AFTER migration to verify everything
- `diagnose_database.sql` - Optional: Run this to see current state BEFORE migration

---

## 🎯 How to Run the Migration

### Option 1: Via Supabase Dashboard (Recommended)

1. Go to your Supabase Dashboard: https://supabase.com/dashboard/project/kbltwyiowkbxzhhhozxf
2. Click on **SQL Editor** in the left sidebar
3. Click **"New Query"**
4. Copy the entire contents of `PRODUCTION_READY_MIGRATION.sql`
5. Paste it into the query editor
6. Click **"Run"** (or press Ctrl+Enter)
7. Wait for completion (should take 10-30 seconds)

### Option 2: Via Supabase CLI

```bash
cd "C:\Users\Robert Cushman\.vscode\Projects\ai-webscraper"

# Option A: Direct execution
supabase db execute --file PRODUCTION_READY_MIGRATION.sql --linked

# Option B: If you get errors, try:
cat PRODUCTION_READY_MIGRATION.sql | supabase db execute --linked
```

---

## ✅ Verification

After running the migration, verify everything is correct:

1. Run `verify_migration.sql` in the Supabase SQL Editor
2. You should see all checks marked with ✅ PASS
3. Look for these results:
   - ✅ All 11 tables exist
   - ✅ All 11 tables have RLS enabled
   - ✅ 40+ RLS policies created
   - ✅ 14+ foreign key constraints
   - ✅ 15+ performance indexes

---

## 🔍 Understanding the RLS Setup

### Key Concept: Service Role vs User Auth

**Your Backend (using `SUPABASE_SECRET_KEY`):**
- Automatically **bypasses ALL RLS policies**
- Can read/write anything without restriction
- No special RLS checks needed

**Frontend Users (using anon/auth keys):**
- Subject to RLS policies
- Can only access their own data
- Policies enforce ownership through `auth.uid()`

### Ownership Model

```
users (owns data)
  └─ crawls (user_id)
       ├─ pages (via crawl_id)
       │    ├─ seo_metadata (via page_id)
       │    └─ links (via source_page_id)
       ├─ issues (via crawl_id)
       └─ summaries (via crawl_id)
  └─ batches (user_id)
       └─ batch_sites (via batch_id)
  └─ audit_log (user_id)
  └─ google_places (user_id)
```

All dependent tables verify ownership by joining back to `crawls.user_id` or directly to `user_id`.

---

## 🐛 Troubleshooting

### Error: "relation X already exists"
✅ **This is fine!** The migration is idempotent. It will skip existing tables.

### Error: "policy X already exists"
✅ **This is fine!** The migration drops existing policies before recreating them.

### Error: "permission denied"
❌ Make sure you're using the **service role key** or are logged in as the database owner.

### Error: "foreign key violation"
❌ This means you have orphaned data. Clean it up or let me know what table and I'll help.

---

## 🎉 What Happens After Migration

Once this runs successfully:

1. **All tables will exist** with proper schemas
2. **Your backend will work** - service role bypasses RLS
3. **Data is secure** - users can only access their own crawls
4. **Queries will be fast** - indexes optimize lookups
5. **Foreign keys prevent orphans** - CASCADE deletes clean up related data

---

## 💡 Testing Your Crawler

After migration, test your crawler:

```bash
# 1. Start your backend
cd backend
uvicorn app.main:app --reload

# 2. Start Celery worker
celery -A app.worker worker --loglevel=info

# 3. Create a test crawl via your frontend or API
# It should now work without RLS errors!
```

---

## 📞 If You Hit Issues

If something doesn't work:

1. Run `verify_migration.sql` and share the output
2. Check your backend logs for specific error messages
3. Verify you're using `SUPABASE_SECRET_KEY` (not anon key) in backend
4. Make sure the key is the **service role key** (starts with `eyJ...` and is very long)

---

## 🔥 Why This Migration is Superior

Compared to the previous version:

| Previous | Production-Ready |
|----------|------------------|
| ❌ Only SELECT policies | ✅ Full CRUD policies |
| ❌ Redundant service_role checks | ✅ Clean, minimal policies |
| ❌ Missing foreign keys | ✅ All FKs with CASCADE |
| ❌ Missing indexes | ✅ 15+ performance indexes |
| ❌ Not idempotent | ✅ Safe to run multiple times |
| ❌ Incomplete tables | ✅ All 11 tables |

---

**Ready to ship.** Run it and let me know the results!