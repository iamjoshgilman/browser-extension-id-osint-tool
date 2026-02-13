#!/bin/bash
set -e

# Fix ownership of mounted volumes (runs as root)
chown -R appuser:appuser /app/data /app/logs

# Drop to non-root user and exec the start script
exec gosu appuser /app/start.sh
