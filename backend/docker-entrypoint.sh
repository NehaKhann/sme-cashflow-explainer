#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q 2>/dev/null; do
  POSTGRES_HOST="${DATABASE_URL#*@}" && POSTGRES_HOST="${POSTGRES_HOST%%:*}"
  POSTGRES_USER="${DATABASE_URL#*://}" && POSTGRES_USER="${POSTGRES_USER%%:*}" && POSTGRES_USER="${POSTGRES_USER#*:}"
  POSTGRES_DB="${DATABASE_URL##*/}"
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
