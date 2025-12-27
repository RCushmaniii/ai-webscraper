# Database Documentation

This directory contains database-related files for the AI WebScraper project.

## Structure

```
database/
├── migrations/          # SQL migration files
│   ├── fix_status_constraint.sql
│   ├── fix_all_rls_policies.sql
│   ├── PRODUCTION_READY_MIGRATION.sql
│   └── ...
└── README.md           # This file
```

## Migrations

All SQL migration files are stored in the `migrations/` folder. These files handle:

- Database schema updates
- RLS (Row Level Security) policy fixes
- Constraint modifications
- Table structure changes

### Key Migration Files

- **`PRODUCTION_READY_MIGRATION.sql`** - Complete production migration script
- **`fix_status_constraint.sql`** - Updates crawl status constraint to include all valid values
- **`fix_all_rls_policies.sql`** - Comprehensive RLS policy fixes
- **`fix_users_table.sql`** - User table structure fixes

### Running Migrations

Migrations should be run directly in your Supabase SQL Editor:

1. Open Supabase Dashboard → SQL Editor
2. Copy the contents of the migration file
3. Execute the SQL
4. Verify the changes

### Migration Order

For a fresh database setup, run migrations in this order:

1. `PRODUCTION_READY_MIGRATION.sql` - Base schema
2. `fix_status_constraint.sql` - Status constraint fix
3. `fix_all_rls_policies.sql` - RLS policies

## Supabase Configuration

The project uses Supabase for:

- PostgreSQL database
- Authentication
- Row Level Security (RLS)
- Real-time subscriptions

See `../DEPLOYMENT_PLAN.md` for complete setup instructions.
