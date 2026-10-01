-- Database initialization script for PostgreSQL

-- 1. Create Admin Role (Read-Write for ETL & Ingestion)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'datapulse_admin') THEN
        CREATE ROLE datapulse_admin WITH LOGIN PASSWORD 'adminpassword';
    END IF;
END
$$;

-- 2. Create Read-Only Role (SELECT-only for API & GenAI Query Engine)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'datapulse_readonly') THEN
        CREATE ROLE datapulse_readonly WITH LOGIN PASSWORD 'readonlypassword';
    END IF;
END
$$;

-- 3. Grant Permissions
GRANT ALL PRIVILEGES ON DATABASE datapulse TO datapulse_admin;
GRANT CONNECT ON DATABASE datapulse TO datapulse_readonly;
GRANT USAGE ON SCHEMA public TO datapulse_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO datapulse_readonly;
