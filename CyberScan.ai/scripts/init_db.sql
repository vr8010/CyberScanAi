-- SecureScout — PostgreSQL initialization script
-- This runs once when the Postgres container is first created.
-- SQLAlchemy handles the actual table creation via create_all().

-- Create extension for UUID generation (optional but useful)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ensure the database exists (it's already created by Docker env vars,
-- but this is a safety net)
SELECT 'SecureScout database initialized' AS status;
