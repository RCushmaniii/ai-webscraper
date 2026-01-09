-- Ensure CASCADE DELETE is properly configured for images table
-- This prevents foreign key violations when crawls are deleted during processing

-- Drop existing foreign key constraint if it exists
ALTER TABLE images DROP CONSTRAINT IF EXISTS images_crawl_id_fkey;
ALTER TABLE images DROP CONSTRAINT IF EXISTS images_page_id_fkey;

-- Re-add foreign key constraints with CASCADE DELETE
ALTER TABLE images
ADD CONSTRAINT images_crawl_id_fkey
FOREIGN KEY (crawl_id) REFERENCES crawls(id)
ON DELETE CASCADE;

ALTER TABLE images
ADD CONSTRAINT images_page_id_fkey
FOREIGN KEY (page_id) REFERENCES pages(id)
ON DELETE CASCADE;

-- Verify the constraints are set correctly
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.table_name = 'images'
    AND tc.constraint_type = 'FOREIGN KEY';
