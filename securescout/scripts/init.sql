-- SecureScout database initialization
-- Run automatically by postgres container on first start

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for faster text search (optional)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Tables are created by SQLAlchemy/Alembic on app startup.
-- This script just sets up extensions and any seed data.

-- ── Seed: Create a default admin user ─────────────────────────────────────
-- Password: Admin@123 (bcrypt hash below)
-- IMPORTANT: Change this password immediately after first login!
-- 
-- INSERT INTO users (id, email, hashed_password, full_name, plan, is_active, is_admin, is_verified)
-- VALUES (
--   uuid_generate_v4(),
--   'admin@securescout.io',
--   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewDzAXoLMH.PVNIG',
--   'Admin User',
--   'pro',
--   true,
--   true,
--   true
-- ) ON CONFLICT (email) DO NOTHING;
