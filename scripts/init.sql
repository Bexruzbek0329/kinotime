-- KinoBot Database Initialization Script
-- This runs automatically on first PostgreSQL container start

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS unaccent; -- For accent-insensitive search

-- Create default superadmin (password: admin123 — CHANGE IN PRODUCTION)
-- Password hash for 'admin123' using bcrypt
-- Run: python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('admin123'))"
-- and replace the hash below with your generated hash
