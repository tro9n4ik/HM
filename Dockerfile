# Stage 1: Build React Admin UI
FROM node:20-slim AS frontend-builder
WORKDIR /app/admin
COPY admin/package.json admin/package-lock.json* ./
RUN npm install
COPY admin/ ./
RUN npm run build

# Stage 2: Build Python Core Backend
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (including pg_isready)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY core/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt psycopg[binary]

# Copy frontend build
COPY --from=frontend-builder /app/core/app/web/static/admin /app/core/app/web/static/admin

# Copy backend code
COPY core /app/core
COPY plugins /app/plugins
COPY docker-entrypoint.sh /app/

# Set working directory to root so entrypoint script can run
WORKDIR /app
CMD ["./docker-entrypoint.sh"]
