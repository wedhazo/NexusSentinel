#!/bin/bash
set -e

# Configuration
MAX_RETRIES=30
RETRY_INTERVAL=2
TIMEOUT=5

# Colors for logging
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date -u +"%Y-%m-%d %H:%M:%S UTC") - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date -u +"%Y-%m-%d %H:%M:%S UTC") - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date -u +"%Y-%m-%d %H:%M:%S UTC") - $1"
}

# Function to check if database is ready
check_db() {
    pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t ${TIMEOUT} > /dev/null 2>&1
}

# Wait for database to be ready
wait_for_db() {
    log_info "Checking database connection: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    local retries=0
    until check_db || [ $retries -eq $MAX_RETRIES ]; do
        retries=$((retries+1))
        log_warn "Waiting for PostgreSQL to be ready... ($retries/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    if [ $retries -eq $MAX_RETRIES ]; then
        log_error "Could not connect to PostgreSQL after $MAX_RETRIES attempts!"
        log_error "Database connection details:"
        log_error "  Host: ${DB_HOST}"
        log_error "  Port: ${DB_PORT}"
        log_error "  User: ${DB_USER}"
        log_error "  Database: ${DB_NAME}"
        log_error "Please check your database configuration and ensure PostgreSQL is running."
        exit 1
    fi
    
    log_info "PostgreSQL is ready! Connected to ${DB_HOST}:${DB_PORT}/${DB_NAME}"
}

# Main execution
log_info "Starting NexusSentinel API entrypoint script"

# Check if database variables are set
if [ -z "${DB_HOST}" ] || [ -z "${DB_PORT}" ] || [ -z "${DB_USER}" ] || [ -z "${DB_NAME}" ]; then
    log_warn "Database environment variables not fully set:"
    log_warn "  DB_HOST=${DB_HOST:-not set}"
    log_warn "  DB_PORT=${DB_PORT:-not set}"
    log_warn "  DB_USER=${DB_USER:-not set}"
    log_warn "  DB_NAME=${DB_NAME:-not set}"
    log_warn "Continuing without database connection check..."
else
    wait_for_db
fi

# Apply database migrations if APPLY_MIGRATIONS is set to true
if [ "${APPLY_MIGRATIONS:-false}" = "true" ]; then
    log_info "Applying database migrations..."
    alembic upgrade head
    if [ $? -eq 0 ]; then
        log_info "Database migrations applied successfully"
    else
        log_error "Failed to apply database migrations"
        exit 1
    fi
fi

# Execute the CMD
log_info "Starting NexusSentinel API service"
exec "$@"
