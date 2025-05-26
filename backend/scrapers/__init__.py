"""
Browser extension scrapers package
"""
from scrapers.chrome import ChromeStoreScraper
from scrapers.firefox import FirefoxAddonsScraper
from scrapers.edge import EdgeAddonsScraper

__all__ = ['ChromeStoreScraper', 'FirefoxAddonsScraper', 'EdgeAddonsScraper']
