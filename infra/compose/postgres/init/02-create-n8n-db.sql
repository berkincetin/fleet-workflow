-- Create a separate database for n8n (task 6.1) so its schema stays isolated
-- from the Fleet application database, same pattern as langfuse's own DB.
-- Runs once, on first Postgres init, via /docker-entrypoint-initdb.d.
CREATE DATABASE n8n;
