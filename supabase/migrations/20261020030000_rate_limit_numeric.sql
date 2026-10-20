-- crawls.rate_limit and batches.rate_limit: INTEGER -> NUMERIC(5,2).
--
-- Why: the crawl form has always accepted fractional requests-per-second
-- (step 0.1, range 0.1-10) and the Pydantic model types the field as float,
-- but the column created in 20251216000359_init_schema.sql is INTEGER.
--
-- History of the mismatch, so nobody "fixes" it back:
--   * 0864680 (2026-01) cast the value to int() in the API before inserting.
--     That made Postgres happy and silently turned 0.5 req/s into 0, which
--     the crawler's RateLimiter then divided by.
--   * 026a922 (2026-10-19, PR #110) restored float() to fix the division by
--     zero, and every crawl creation in production failed with
--     'invalid input syntax for type integer: "1.0"' (Postgres 22P02).
--
-- The column is the only place that disagreed with the product, so the
-- column changes. NUMERIC(5,2) covers 0.10-999.99; the API caps at 10.
-- The rewrite is instant at this table size and PostgREST reloads its
-- schema cache on DDL, so no backend restart is needed.
--
-- Rollback (loses the fraction, never fails):
--   ALTER TABLE crawls  ALTER COLUMN rate_limit TYPE INTEGER USING round(rate_limit);
--   ALTER TABLE batches ALTER COLUMN rate_limit TYPE INTEGER USING round(rate_limit);

ALTER TABLE crawls
  ALTER COLUMN rate_limit TYPE NUMERIC(5,2) USING rate_limit::numeric;

ALTER TABLE batches
  ALTER COLUMN rate_limit TYPE NUMERIC(5,2) USING rate_limit::numeric;

COMMENT ON COLUMN crawls.rate_limit IS
  'Requests per second the crawler may send to the target host (0.1-10). NUMERIC since 2026-10-20; was INTEGER, which could not store the fractional values the form accepts.';

COMMENT ON COLUMN batches.rate_limit IS
  'Requests per second applied to each crawl in the batch (0.1-10). NUMERIC since 2026-10-20.';
