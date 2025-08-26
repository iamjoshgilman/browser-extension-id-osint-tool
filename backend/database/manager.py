"""
Database management for extension caching
"""
import sqlite3
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from contextlib import contextmanager
from models.extension import ExtensionData
from config import get_config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = None):
        config = get_config()
        self.db_path = db_path or config.DATABASE_PATH
        self.cache_expiry_days = config.DATABASE_CACHE_EXPIRY_DAYS
        # Ensure the directory for the database exists. Without this SQLite
        # will raise an OperationalError when attempting to open the database
        # if the directory component of the path has not been created yet.
        # This mirrors the behaviour of other parts of the application which
        # expect the database file to be created on demand.
        if self.db_path != ":memory:":
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create extensions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extension_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension_id VARCHAR(255) NOT NULL,
                    store VARCHAR(50) NOT NULL,
                    name VARCHAR(500),
                    publisher VARCHAR(255),
                    description TEXT,
                    version VARCHAR(50),
                    user_count VARCHAR(50),
                    category VARCHAR(100),
                    rating VARCHAR(20),
                    rating_count VARCHAR(50),
                    last_updated VARCHAR(50),
                    store_url TEXT,
                    icon_url TEXT,
                    homepage_url TEXT,
                    privacy_policy_url TEXT,
                    permissions TEXT,
                    found BOOLEAN DEFAULT 1,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(extension_id, store)
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_extension_store 
                ON extension_cache(extension_id, store)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scraped_at 
                ON extension_cache(scraped_at)
            ''')
            
            # Create search history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension_id VARCHAR(255) NOT NULL,
                    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    found_in_stores TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def get_from_cache(self, extension_id: str, store: str) -> Optional[ExtensionData]:
        """Retrieve extension from cache if not expired"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate cache expiry. A value of 0 means the cache should
            # expire immediately while negative values disable expiry checks
            # altogether.
            if self.cache_expiry_days is not None and self.cache_expiry_days >= 0:
                cache_expiry = datetime.now() - timedelta(days=self.cache_expiry_days)
                expiry_clause = "AND scraped_at > ?"
                params = (extension_id, store, cache_expiry.isoformat())
            else:
                expiry_clause = ""
                params = (extension_id, store)
            
            cursor.execute(f'''
                SELECT * FROM extension_cache
                WHERE extension_id = ? AND store = ? {expiry_clause}
            ''', params)
            
            row = cursor.fetchone()
            
            if row:
                # Convert row to dictionary
                data = dict(row)
                
                # Parse permissions from JSON string
                if data.get('permissions'):
                    try:
                        data['permissions'] = json.loads(data['permissions'])
                    except:
                        data['permissions'] = []
                else:
                    data['permissions'] = []
                
                # Remove database-specific fields
                data.pop('id', None)
                data['store_source'] = data.pop('store', store)
                
                return ExtensionData.from_dict(data)
        
        return None
    
    def save_to_cache(self, extension_data: ExtensionData):
        """Save extension data to cache"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert permissions list to JSON string
            permissions_json = json.dumps(extension_data.permissions) if extension_data.permissions else "[]"
            
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO extension_cache
                    (extension_id, store, name, publisher, description, version,
                     user_count, category, rating, rating_count, last_updated, 
                     store_url, icon_url, homepage_url, privacy_policy_url,
                     permissions, found, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    extension_data.extension_id,
                    extension_data.store_source,
                    extension_data.name,
                    extension_data.publisher,
                    extension_data.description,
                    extension_data.version,
                    extension_data.user_count,
                    extension_data.category,
                    extension_data.rating,
                    extension_data.rating_count,
                    extension_data.last_updated,
                    extension_data.store_url,
                    extension_data.icon_url,
                    extension_data.homepage_url,
                    extension_data.privacy_policy_url,
                    permissions_json,
                    extension_data.found,
                    datetime.now().isoformat()
                ))
                conn.commit()
                logger.info(f"Saved to cache: {extension_data.name} ({extension_data.store_source})")
            except Exception as e:
                logger.error(f"Error saving to cache: {e}")
    
    def log_search(self, extension_id: str, found_in_stores: List[str], 
                   ip_address: str = None, user_agent: str = None):
        """Log search history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO search_history 
                (extension_id, found_in_stores, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (
                extension_id,
                ','.join(found_in_stores),
                ip_address,
                user_agent
            ))
            conn.commit()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total cached extensions
            cursor.execute('SELECT COUNT(*) FROM extension_cache')
            stats['total_cached'] = cursor.fetchone()[0]
            
            # By store
            cursor.execute('''
                SELECT store, COUNT(*) 
                FROM extension_cache 
                GROUP BY store
            ''')
            stats['by_store'] = dict(cursor.fetchall())
            
            # Unique extensions
            cursor.execute('SELECT COUNT(DISTINCT extension_id) FROM extension_cache')
            stats['unique_extensions'] = cursor.fetchone()[0]
            
            # Cache hit rate (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute('''
                SELECT COUNT(*) FROM search_history 
                WHERE search_timestamp > ?
            ''', (yesterday,))
            recent_searches = cursor.fetchone()[0]
            stats['searches_24h'] = recent_searches
            
            # Most searched extensions
            cursor.execute('''
                SELECT extension_id, COUNT(*) as count 
                FROM search_history 
                GROUP BY extension_id 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            stats['top_searched'] = [
                {'extension_id': row[0], 'count': row[1]} 
                for row in cursor.fetchall()
            ]
            
            return stats
    
    def cleanup_old_cache(self, days: int = None):
        """Remove cache entries older than specified days"""
        if days is None:
            days = self.cache_expiry_days * 2  # Clean up entries twice as old as expiry
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                DELETE FROM extension_cache 
                WHERE scraped_at < ?
            ''', (cutoff_date,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted} old cache entries")
            return deleted
