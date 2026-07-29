#!/bin/sh
set -e

# Parse connection details from DATABASE_URL once
# Expected format: postgresql+asyncpg://user:pass@host:port/db
_HOST="${DATABASE_URL#*@}" && _HOST="${_HOST%%:*}"
_USER="${DATABASE_URL#*://}" && _USER="${_USER%%:*}"
_DB="${DATABASE_URL##*/}"

echo "Waiting for PostgreSQL at ${_HOST}..."
until pg_isready -h "$_HOST" -U "$_USER" -d "$_DB" -q 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

echo "Creating database tables..."
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
