#!/bin/bash
set -e

echo "Starting Home.Media..."
if [ ! -f .env ]; then
    echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
    echo "Generated .env file with SECRET_KEY"
fi

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

docker compose up --build -d
echo "Home.Media started successfully. Access it at http://localhost:8142"
