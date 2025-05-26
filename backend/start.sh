#!/bin/bash

# Startup script for Browser Extension OSINT Tool Backend

echo "Starting Browser Extension OSINT Tool Backend..."

# Ensure we're in the correct directory
cd /app

# Set Python path
export PYTHONPATH=/app:$PYTHONPATH

# Debug information
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Directory contents:"
ls -la

# Create necessary directories
mkdir -p data logs

# Start the application
exec gunicorn --bind 0.0.0.0:5000 --workers ${WORKERS:-4} wsgi:app
