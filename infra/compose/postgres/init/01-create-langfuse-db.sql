-- Create a separate database for Langfuse so its schema stays isolated from the
-- Fleet application database (Alembic migrations own `fleet`; Langfuse owns `langfuse`).
-- Runs once, on first Postgres init, via /docker-entrypoint-initdb.d.
CREATE DATABASE langfuse;
