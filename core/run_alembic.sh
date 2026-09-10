#!/bin/bash
cd /app/core
source venv/bin/activate
alembic upgrade head
