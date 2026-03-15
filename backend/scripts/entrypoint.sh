#!/bin/sh
set -e

echo "==> Running migrations..."
alembic upgrade head || echo "==> Migrations skipped (already applied or running concurrently)"

echo "==> Running seed..."
python scripts/seed.py || echo "==> Seed skipped"

echo "==> Starting $@"
exec "$@"
