#!/bin/bash

# Browser Extension OSINT Tool Setup Script

echo "🔍 Browser Extension OSINT Tool Setup"
echo "===================================="

# Check if running from project root
if [ ! -f "docker/docker-compose.yml" ]; then
  echo "❌ Error: Please run this script from the project root directory"
  exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/scrapers backend/models backend/database
mkdir -p frontend/css frontend/js
mkdir -p docker nginx
mkdir -p data logs
mkdir -p scripts tests

# Create __init__.py files for Python packages
echo "📝 Creating Python package files..."
touch backend/__init__.py
touch backend/scrapers/__init__.py
touch backend/models/__init__.py
touch backend/database/__init__.py

# Copy environment file if not exists
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    echo "📋 Copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  Please edit .env and set your configuration values"
  else
    echo "⚠️  No .env.example found. Creating basic .env file..."
    cat >.env <<EOF
# Application Settings
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-string
DEBUG=True

# API Settings
API_KEY_REQUIRED=False
API_KEY=your-api-key-here
API_RATE_LIMIT=100/hour

# Database
DATABASE_PATH=data/extensions_cache.db
CACHE_EXPIRY_DAYS=7

# Scraping
SCRAPER_TIMEOUT=15
SCRAPER_DELAY=1.0

# CORS
CORS_ORIGINS=http://localhost,http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
    echo "✅ Created .env file with default values"
  fi
fi

# Set permissions
echo "🔒 Setting permissions..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod 755 data logs

# Check Docker installation
if command -v docker &>/dev/null && command -v docker-compose &>/dev/null; then
  echo "🐳 Docker and Docker Compose detected"
  echo ""
  echo "To start with Docker:"
  echo "  cd docker && docker-compose up -d"
  echo ""
else
  echo "⚠️  Docker not detected. For manual setup:"
  echo "  1. Install Python 3.11+"
  echo "  2. cd backend && pip install -r requirements.txt"
  echo "  3. python app.py"
  echo ""
fi

# Generate a random API key if needed
if grep -q "your-api-key-here" .env; then
  NEW_API_KEY=$(openssl rand -hex 32 2>/dev/null || python -c 'import secrets; print(secrets.token_hex(32))')
  if [ ! -z "$NEW_API_KEY" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      sed -i '' "s/your-api-key-here/$NEW_API_KEY/g" .env
    else
      # Linux
      sed -i "s/your-api-key-here/$NEW_API_KEY/g" .env
    fi
    echo "🔑 Generated new API key in .env"
  fi
fi

# Generate a random secret key if needed
if grep -q "change-this-to-a-random-string" .env; then
  NEW_SECRET=$(openssl rand -hex 32 2>/dev/null || python -c 'import secrets; print(secrets.token_hex(32))')
  if [ ! -z "$NEW_SECRET" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      sed -i '' "s/change-this-to-a-random-string/$NEW_SECRET/g" .env
    else
      # Linux
      sed -i "s/change-this-to-a-random-string/$NEW_SECRET/g" .env
    fi
    echo "🔐 Generated new secret key in .env"
  fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and edit .env file if needed"
echo "2. Place all Python files in their respective directories"
echo "3. Start the application:"
echo "   - With Docker: cd docker && docker-compose up -d"
echo "   - Without Docker: cd backend && python app.py"
echo ""
echo "📖 See README.md for more details"
