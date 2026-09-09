#!/bin/bash
set -e

DATA_DIR=${DATA_DIR:-/app/data}
ENV_FILE="${DATA_DIR}/.env_secrets"

# Generate SECRET_KEY if not exists
if [ ! -f "$ENV_FILE" ]; then
    echo "SECRET_KEY=$(openssl rand -hex 32)" > "$ENV_FILE"
    echo "Generated new SECRET_KEY in $ENV_FILE"
fi

# Load SECRET_KEY
set -a; source "$ENV_FILE"; set +a

# Create directory for plugins
mkdir -p "${DATA_DIR}/plugins"

# Wait for DB if it's Postgres
if [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Waiting for database..."
    # pg_isready doesn't like postgresql+psycopg scheme. Strip it.
    CLEAN_URL=$(echo "$DATABASE_URL" | sed 's/+psycopg//')
    while ! pg_isready -d "$CLEAN_URL" > /dev/null 2> /dev/null; do
        sleep 1
    done
    echo "Database is ready."
fi

# Run migrations
echo "Running database migrations..."
cd /app/core
alembic upgrade head

# Start uvicorn
echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8142
