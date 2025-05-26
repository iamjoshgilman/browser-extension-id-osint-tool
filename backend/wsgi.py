#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run()
