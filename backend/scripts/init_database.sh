#!/bin/bash
#
# Database initialization script for ResuMate
#
# Usage:
#   ./scripts/init_database.sh
#

set -e

echo "🚀 Starting ResuMate database initialization..."
echo ""

# Detect Docker Compose command (V2 'docker compose' or V1 'docker-compose')
DOCKER_COMPOSE_CMD=""
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "ℹ️  Using Docker Compose V2 (modern)"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "ℹ️  Using Docker Compose V1 (legacy)"
else
    echo "❌ Error: Neither Docker Compose V1 nor V2 found"
    echo "   Please install Docker Desktop or Docker Compose"
    exit 1
fi

# Check if services are running
if ! $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
    echo "📦 Starting Docker services..."
    $DOCKER_COMPOSE_CMD up -d
    echo ""
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Set database URL for Alembic (sync driver for migrations)
# Note: Using port 5433 to avoid conflict with native PostgreSQL on host
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql://resumate_user:resumate_password@localhost:5433/resumate"
    echo "ℹ️  Using default DATABASE_URL"
fi

echo "📍 Database URL: $DATABASE_URL"
echo ""

# Change to backend directory (script is in backend/scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Run Alembic migrations
echo "🔄 Running database migrations..."
source .venv/bin/activate
alembic upgrade head

echo ""
echo "✅ Database initialization complete!"
echo ""
echo "📊 Tables created:"
echo "   - resumes"
echo "   - parsed_resume_data"
echo "   - resume_corrections"
echo "   - resume_shares"
echo ""
echo "🎉 Ready to use database!"
