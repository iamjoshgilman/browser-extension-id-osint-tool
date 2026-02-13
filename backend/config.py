"""
Configuration settings for the Extension OSINT Tool
"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Application
    APP_NAME = "Browser Extension OSINT Tool"
    VERSION = "1.0.0"

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

    # Database
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/extensions_cache.db")
    DATABASE_CACHE_EXPIRY_DAYS = int(os.environ.get("CACHE_EXPIRY_DAYS", "7"))

    # API
    API_RATE_LIMIT = os.environ.get("API_RATE_LIMIT", "100/hour")
    API_KEY_REQUIRED = os.environ.get("API_KEY_REQUIRED", "False").lower() == "true"
    API_KEY = os.environ.get("API_KEY", "")

    # Scraping
    SCRAPER_TIMEOUT = int(os.environ.get("SCRAPER_TIMEOUT", "15"))
    SCRAPER_DELAY = float(os.environ.get("SCRAPER_DELAY", "1.0"))
    SCRAPER_USER_AGENT = os.environ.get(
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")

    # Cache
    REDIS_URL = os.environ.get("REDIS_URL", None)  # Optional Redis for distributed caching

    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    DATABASE_PATH = "data/dev_extensions_cache.db"


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    # Note: API_KEY_REQUIRED is inherited from base Config class
    # which reads from environment variable

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Log to syslog in production (optional)
        import logging
        from logging.handlers import SysLogHandler

        if os.path.exists("/dev/log"):
            syslog_handler = SysLogHandler(address="/dev/log")
            syslog_handler.setLevel(logging.WARNING)
            app.logger.addHandler(syslog_handler)


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DATABASE_PATH = ":memory:"
    DATABASE_CACHE_EXPIRY_DAYS = 0


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get("FLASK_ENV", "development")
    return config.get(env, config["default"])
