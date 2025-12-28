# Database Migrations

This directory contains SQL migration scripts for the AI WebScraper database.

## How to Apply Migrations

### Using Supabase Dashboard (Recommended)
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy and paste the migration SQL
5. Execute the query

### Using psql CLI
```bash
psql -h <your-supabase-host> -U postgres -d postgres -f migrations/001_add_images_table.sql
psql -h <your-supabase-host> -U postgres -d postgres -f migrations/002_add_full_content_column.sql
```

### Using Supabase CLI
```bash
supabase db push
```

## Migration Order

**IMPORTANT**: Apply migrations in numerical order:

1. `001_add_images_table.sql` - Creates images table
2. `002_add_full_content_column.sql` - Adds full_content to pages

## Rollback

If you need to rollback a migration:

### Rollback 002 (full_content column)
```sql
ALTER TABLE pages DROP COLUMN IF EXISTS full_content;
DROP INDEX IF EXISTS idx_pages_full_content_fts;
```

### Rollback 001 (images table)
```sql
DROP POLICY IF EXISTS "Users can view their own images" ON images;
DROP INDEX IF EXISTS idx_images_crawl_id;
DROP INDEX IF EXISTS idx_images_page_id;
DROP INDEX IF EXISTS idx_images_is_broken;
DROP INDEX IF EXISTS idx_images_has_alt;
DROP TABLE IF EXISTS images;
```

## Verification

After applying migrations, verify with:

```sql
-- Check images table exists
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'images';

-- Check full_content column exists
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'pages' AND column_name = 'full_content';

-- Check indexes
SELECT indexname FROM pg_indexes WHERE tablename IN ('images', 'pages');
```

## Current Migrations

| # | File | Description | Status |
|---|------|-------------|--------|
| 001 | `001_add_images_table.sql` | Creates images table with RLS | ⏳ Pending |
| 002 | `002_add_full_content_column.sql` | Adds full_content to pages | ⏳ Pending |

## Notes

- All migrations include RLS policies for security
- Indexes are created for performance
- All migrations are idempotent (safe to run multiple times)
- Always backup your database before running migrations