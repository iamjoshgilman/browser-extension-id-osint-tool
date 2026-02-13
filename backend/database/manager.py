"""
Database management for extension caching
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from contextlib import contextmanager
from models.extension import ExtensionData
from models.api_key import ApiKeyData
from config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations"""

    def __init__(self, db_path: str = None):
        config = get_config()
        self.db_path = db_path or config.DATABASE_PATH
        self.cache_expiry_days = config.DATABASE_CACHE_EXPIRY_DAYS
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

            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")

            # Create extensions table
            cursor.execute(
                """
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
            """
            )

            # Create indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_extension_store
                ON extension_cache(extension_id, store)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scraped_at
                ON extension_cache(scraped_at)
            """
            )

            # Create search history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension_id VARCHAR(255) NOT NULL,
                    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    found_in_stores TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
            """
            )

            # Create extension snapshots table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS extension_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension_id VARCHAR(255) NOT NULL,
                    store VARCHAR(50) NOT NULL,
                    version VARCHAR(50),
                    permissions TEXT,
                    name VARCHAR(500),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_ext_store
                ON extension_snapshots(extension_id, store)
            """
            )

            # Create API keys table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash VARCHAR(64) NOT NULL UNIQUE,
                    key_prefix VARCHAR(8) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT DEFAULT '',
                    created_by VARCHAR(255) DEFAULT '',
                    rate_limit_per_minute INTEGER DEFAULT 30,
                    rate_limit_per_hour INTEGER DEFAULT 500,
                    is_active BOOLEAN DEFAULT 1,
                    permissions TEXT DEFAULT '["search","bulk-search","search-by-name"]',
                    last_used_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    revoked_at TIMESTAMP
                )
            """
            )

            # Create API usage log table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id INTEGER,
                    endpoint VARCHAR(255) NOT NULL,
                    method VARCHAR(10) NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    request_params TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_key_created
                ON api_usage_log(api_key_id, created_at)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_endpoint
                ON api_usage_log(endpoint)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_usage_created
                ON api_usage_log(created_at)
            """
            )

            # Create bulk jobs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bulk_jobs (
                    id VARCHAR(36) PRIMARY KEY,
                    api_key_id INTEGER,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    extension_ids TEXT NOT NULL,
                    stores TEXT NOT NULL,
                    include_permissions BOOLEAN DEFAULT 0,
                    total_tasks INTEGER NOT NULL,
                    completed_tasks INTEGER DEFAULT 0,
                    failed_tasks INTEGER DEFAULT 0,
                    results TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """
            )

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def get_from_cache(self, extension_id: str, store: str) -> Optional[ExtensionData]:
        """Retrieve extension from cache if not expired"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Calculate cache expiry
            if self.cache_expiry_days > 0:
                cache_expiry = datetime.now() - timedelta(days=self.cache_expiry_days)
                expiry_clause = "AND scraped_at > ?"
                params = (extension_id, store, cache_expiry.isoformat())
            else:
                expiry_clause = ""
                params = (extension_id, store)

            cursor.execute(
                f"""
                SELECT * FROM extension_cache
                WHERE extension_id = ? AND store = ? {expiry_clause}
            """,
                params,
            )

            row = cursor.fetchone()

            if row:
                # Convert row to dictionary
                data = dict(row)

                # Parse permissions from JSON string
                if data.get("permissions"):
                    try:
                        data["permissions"] = json.loads(data["permissions"])
                    except Exception:
                        data["permissions"] = []
                else:
                    data["permissions"] = []

                # Remove database-specific fields
                data.pop("id", None)
                data["store_source"] = data.pop("store", store)

                return ExtensionData.from_dict(data)

        return None

    def get_previous_found_entry(self, extension_id: str, store: str) -> Optional[ExtensionData]:
        """
        Retrieve previous cache entry where found=True (ignoring expiry).
        This should be called BEFORE saving a new found=False entry.
        Since we use INSERT OR REPLACE with UNIQUE constraint, old data is overwritten.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get the current entry - if it has found=False but has actual data,
            # it means we previously found it
            cursor.execute(
                """
                SELECT * FROM extension_cache
                WHERE extension_id = ? AND store = ?
            """,
                (extension_id, store),
            )

            row = cursor.fetchone()

            if row:
                data = dict(row)

                # If current entry is found=False but has a name, it was previously found
                # This won't work well - we need to check if found=1
                if data.get("found") == 1:
                    # Parse permissions from JSON string
                    if data.get("permissions"):
                        try:
                            data["permissions"] = json.loads(data["permissions"])
                        except Exception:
                            data["permissions"] = []
                    else:
                        data["permissions"] = []

                    # Remove database-specific fields
                    data.pop("id", None)
                    data["store_source"] = data.pop("store", store)

                    return ExtensionData.from_dict(data)

        return None

    def save_to_cache(self, extension_data: ExtensionData):
        """Save extension data to cache"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Convert permissions list to JSON string
            permissions_json = (
                json.dumps(extension_data.permissions) if extension_data.permissions else "[]"
            )

            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO extension_cache
                    (extension_id, store, name, publisher, description, version,
                     user_count, category, rating, rating_count, last_updated,
                     store_url, icon_url, homepage_url, privacy_policy_url,
                     permissions, found, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
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
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.info(
                    f"Saved to cache: {extension_data.name} ({extension_data.store_source})"
                )

                # Save snapshot if extension was found
                if extension_data.found:
                    self.save_snapshot_if_changed(extension_data)

            except Exception as e:
                logger.error(f"Error saving to cache: {e}")

    def log_search(
        self,
        extension_id: str,
        found_in_stores: List[str],
        ip_address: str = None,
        user_agent: str = None,
    ):
        """Log search history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO search_history
                (extension_id, found_in_stores, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            """,
                (extension_id, ",".join(found_in_stores), ip_address, user_agent),
            )
            conn.commit()

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total cached extensions
            cursor.execute("SELECT COUNT(*) FROM extension_cache")
            stats["total_cached"] = cursor.fetchone()[0]

            # By store
            cursor.execute(
                """
                SELECT store, COUNT(*)
                FROM extension_cache
                GROUP BY store
            """
            )
            stats["by_store"] = dict(cursor.fetchall())

            # Unique extensions
            cursor.execute("SELECT COUNT(DISTINCT extension_id) FROM extension_cache")
            stats["unique_extensions"] = cursor.fetchone()[0]

            # Cache hit rate (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute(
                """
                SELECT COUNT(*) FROM search_history
                WHERE search_timestamp > ?
            """,
                (yesterday,),
            )
            recent_searches = cursor.fetchone()[0]
            stats["searches_24h"] = recent_searches

            # Most searched extensions
            cursor.execute(
                """
                SELECT extension_id, COUNT(*) as count
                FROM search_history
                GROUP BY extension_id
                ORDER BY count DESC
                LIMIT 10
            """
            )
            stats["top_searched"] = [
                {"extension_id": row[0], "count": row[1]} for row in cursor.fetchall()
            ]

            return stats

    def cleanup_old_cache(self, days: int = None):
        """Remove cache entries older than specified days"""
        if days is None:
            days = self.cache_expiry_days * 2  # Clean up entries twice as old as expiry

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute(
                """
                DELETE FROM extension_cache
                WHERE scraped_at < ?
            """,
                (cutoff_date,),
            )

            deleted = cursor.rowcount
            conn.commit()

            logger.info(f"Cleaned up {deleted} old cache entries")
            return deleted

    def cleanup_old_search_history(self, days: int = 30):
        """Delete search history entries older than specified days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute("DELETE FROM search_history WHERE search_timestamp < ?", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted} old search history entries")
            return deleted

    def save_snapshot_if_changed(self, extension_data: ExtensionData):
        """Save a snapshot if version, permissions, or name has changed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get most recent snapshot for this extension
            cursor.execute(
                """
                SELECT version, permissions, name
                FROM extension_snapshots
                WHERE extension_id = ? AND store = ?
                ORDER BY scraped_at DESC
                LIMIT 1
            """,
                (extension_data.extension_id, extension_data.store_source),
            )

            row = cursor.fetchone()

            # Determine if we should save a new snapshot
            should_save = False

            if not row:
                # No previous snapshot exists
                should_save = True
            else:
                prev_version = row["version"]
                prev_permissions_str = row["permissions"]
                prev_name = row["name"]

                # Parse previous permissions
                try:
                    prev_permissions = (
                        json.loads(prev_permissions_str) if prev_permissions_str else []
                    )
                except Exception:
                    prev_permissions = []

                # Sort permissions for comparison
                curr_permissions_sorted = sorted(extension_data.permissions or [])
                prev_permissions_sorted = sorted(prev_permissions)

                # Check if anything changed
                if (
                    extension_data.version != prev_version
                    or curr_permissions_sorted != prev_permissions_sorted
                    or extension_data.name != prev_name
                ):
                    should_save = True

            # Save snapshot if needed
            if should_save:
                permissions_json = (
                    json.dumps(extension_data.permissions) if extension_data.permissions else "[]"
                )

                cursor.execute(
                    """
                    INSERT INTO extension_snapshots
                    (extension_id, store, version, permissions, name, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        extension_data.extension_id,
                        extension_data.store_source,
                        extension_data.version,
                        permissions_json,
                        extension_data.name,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.info(
                    f"Saved snapshot for {extension_data.extension_id} "
                    f"({extension_data.store_source})"
                )

    def get_extension_history(self, extension_id: str, store: str) -> List[Dict]:
        """Get historical snapshots for an extension"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT version, permissions, name, scraped_at
                FROM extension_snapshots
                WHERE extension_id = ? AND store = ?
                ORDER BY scraped_at ASC
            """,
                (extension_id, store),
            )

            rows = cursor.fetchall()

            history = []
            for row in rows:
                # Parse permissions from JSON
                try:
                    permissions = json.loads(row["permissions"]) if row["permissions"] else []
                except Exception:
                    permissions = []

                history.append(
                    {
                        "version": row["version"],
                        "permissions": permissions,
                        "name": row["name"],
                        "scraped_at": row["scraped_at"],
                    }
                )

            return history

    def create_api_key(
        self,
        key_hash: str,
        key_prefix: str,
        name: str,
        description: str = "",
        created_by: str = "",
        rate_limit_per_minute: int = 30,
        rate_limit_per_hour: int = 500,
        permissions: List[str] = None,
        expires_at: Optional[str] = None,
    ) -> int:
        """Create a new API key and return its ID"""
        if permissions is None:
            permissions = ["search", "bulk-search", "search-by-name"]

        with self.get_connection() as conn:
            cursor = conn.cursor()

            permissions_json = json.dumps(permissions)

            cursor.execute(
                """
                INSERT INTO api_keys
                (key_hash, key_prefix, name, description, created_by,
                 rate_limit_per_minute, rate_limit_per_hour, permissions, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    key_hash,
                    key_prefix,
                    name,
                    description,
                    created_by,
                    rate_limit_per_minute,
                    rate_limit_per_hour,
                    permissions_json,
                    expires_at,
                ),
            )
            conn.commit()
            logger.info(f"Created API key: {name} (prefix: {key_prefix})")
            return cursor.lastrowid

    def get_api_key_by_hash(self, key_hash: str) -> Optional[ApiKeyData]:
        """Get API key by hash for authentication validation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM api_keys WHERE key_hash = ?
            """,
                (key_hash,),
            )

            row = cursor.fetchone()

            if row:
                data = dict(row)

                # Parse permissions from JSON string
                if data.get("permissions"):
                    try:
                        data["permissions"] = json.loads(data["permissions"])
                    except Exception:
                        data["permissions"] = ["search", "bulk-search", "search-by-name"]
                else:
                    data["permissions"] = ["search", "bulk-search", "search-by-name"]

                return ApiKeyData.from_dict(data)

        return None

    def list_api_keys(self) -> List[ApiKeyData]:
        """List all non-revoked API keys"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM api_keys WHERE revoked_at IS NULL
                ORDER BY created_at DESC
            """
            )

            rows = cursor.fetchall()
            keys = []

            for row in rows:
                data = dict(row)

                # Parse permissions from JSON string
                if data.get("permissions"):
                    try:
                        data["permissions"] = json.loads(data["permissions"])
                    except Exception:
                        data["permissions"] = ["search", "bulk-search", "search-by-name"]
                else:
                    data["permissions"] = ["search", "bulk-search", "search-by-name"]

                keys.append(ApiKeyData.from_dict(data))

            return keys

    def get_api_key(self, key_id: int) -> Optional[ApiKeyData]:
        """Get API key by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM api_keys WHERE id = ?
            """,
                (key_id,),
            )

            row = cursor.fetchone()

            if row:
                data = dict(row)

                # Parse permissions from JSON string
                if data.get("permissions"):
                    try:
                        data["permissions"] = json.loads(data["permissions"])
                    except Exception:
                        data["permissions"] = ["search", "bulk-search", "search-by-name"]
                else:
                    data["permissions"] = ["search", "bulk-search", "search-by-name"]

                return ApiKeyData.from_dict(data)

        return None

    def update_api_key(self, key_id: int, **kwargs):
        """Update API key fields"""
        allowed_fields = [
            "name",
            "description",
            "rate_limit_per_minute",
            "rate_limit_per_hour",
            "is_active",
            "permissions",
            "last_used_at",
            "expires_at",
        ]

        # Filter to only allowed fields
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return

        # Convert permissions list to JSON if present
        if "permissions" in update_fields:
            update_fields["permissions"] = json.dumps(update_fields["permissions"])

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build SET clause
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values())
            values.append(key_id)

            cursor.execute(
                f"""
                UPDATE api_keys SET {set_clause} WHERE id = ?
            """,
                values,
            )
            conn.commit()
            logger.info(f"Updated API key ID {key_id}")

    def revoke_api_key(self, key_id: int):
        """Revoke an API key"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE api_keys
                SET revoked_at = ?, is_active = 0
                WHERE id = ?
            """,
                (datetime.now().isoformat(), key_id),
            )
            conn.commit()
            logger.info(f"Revoked API key ID {key_id}")

    def log_api_usage(
        self,
        api_key_id: Optional[int],
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_params: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Log API usage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO api_usage_log
                (api_key_id, endpoint, method, status_code, response_time_ms,
                 ip_address, user_agent, request_params, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    api_key_id,
                    endpoint,
                    method,
                    status_code,
                    response_time_ms,
                    ip_address,
                    user_agent,
                    request_params,
                    error_message,
                ),
            )
            conn.commit()

    def get_usage_stats(self, key_id: Optional[int] = None, period_hours: int = 24) -> dict:
        """Get usage statistics with breakdowns by endpoint, status, key, and timeline"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff = (datetime.now() - timedelta(hours=period_hours)).isoformat()

            # Build WHERE clause
            where_clause = "WHERE created_at > ?"
            params = [cutoff]

            if key_id is not None:
                where_clause += " AND api_key_id = ?"
                params.append(key_id)

            # Total requests
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM api_usage_log {where_clause}
            """,
                params,
            )
            total_requests = cursor.fetchone()[0]

            # By endpoint
            cursor.execute(
                f"""
                SELECT endpoint, COUNT(*) as count
                FROM api_usage_log {where_clause}
                GROUP BY endpoint
                ORDER BY count DESC
            """,
                params,
            )
            by_endpoint = dict(cursor.fetchall())

            # By status code
            cursor.execute(
                f"""
                SELECT status_code, COUNT(*) as count
                FROM api_usage_log {where_clause}
                GROUP BY status_code
                ORDER BY count DESC
            """,
                params,
            )
            by_status = {str(row[0]): row[1] for row in cursor.fetchall()}

            # By API key (if not filtered by key_id)
            by_key = {}
            if key_id is None:
                cursor.execute(
                    f"""
                    SELECT api_key_id, COUNT(*) as count
                    FROM api_usage_log {where_clause}
                    GROUP BY api_key_id
                    ORDER BY count DESC
                """,
                    params,
                )
                by_key = {
                    str(row[0]) if row[0] is not None else "anonymous": row[1]
                    for row in cursor.fetchall()
                }

            # Hourly timeline
            cursor.execute(
                f"""
                SELECT strftime('%Y-%m-%d %H:00:00', created_at) as hour, COUNT(*) as count
                FROM api_usage_log {where_clause}
                GROUP BY hour
                ORDER BY hour ASC
            """,
                params,
            )
            timeline = [{"hour": row[0], "count": row[1]} for row in cursor.fetchall()]

            # Average response time
            cursor.execute(
                f"""
                SELECT AVG(response_time_ms) FROM api_usage_log
                {where_clause} AND response_time_ms IS NOT NULL
            """,
                params,
            )
            avg_response_time = cursor.fetchone()[0] or 0

            return {
                "total_requests": total_requests,
                "by_endpoint": by_endpoint,
                "by_status": by_status,
                "by_key": by_key,
                "timeline": timeline,
                "avg_response_time_ms": round(avg_response_time, 2),
                "period_hours": period_hours,
            }

    def get_key_usage_24h(self, key_id: int) -> int:
        """Get usage count for a key in the last 24 hours"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()

            cursor.execute(
                """
                SELECT COUNT(*) FROM api_usage_log
                WHERE api_key_id = ? AND created_at > ?
            """,
                (key_id, cutoff),
            )

            return cursor.fetchone()[0]

    def create_bulk_job(
        self,
        job_id: str,
        api_key_id: Optional[int],
        extension_ids: List[str],
        stores: List[str],
        include_permissions: bool,
        total_tasks: int,
    ) -> str:
        """Create a new bulk job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            extension_ids_json = json.dumps(extension_ids)
            stores_json = json.dumps(stores)

            cursor.execute(
                """
                INSERT INTO bulk_jobs
                (id, api_key_id, extension_ids, stores, include_permissions, total_tasks)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    job_id,
                    api_key_id,
                    extension_ids_json,
                    stores_json,
                    include_permissions,
                    total_tasks,
                ),
            )
            conn.commit()
            logger.info(f"Created bulk job {job_id} with {total_tasks} tasks")
            return job_id

    def update_bulk_job(self, job_id: str, **kwargs):
        """Update bulk job fields"""
        allowed_fields = [
            "status",
            "completed_tasks",
            "failed_tasks",
            "results",
            "error_message",
            "started_at",
            "completed_at",
        ]

        # Filter to only allowed fields
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return

        # Convert results to JSON if present
        if "results" in update_fields and update_fields["results"] is not None:
            update_fields["results"] = json.dumps(update_fields["results"])

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build SET clause
            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values())
            values.append(job_id)

            cursor.execute(
                f"""
                UPDATE bulk_jobs SET {set_clause} WHERE id = ?
            """,
                values,
            )
            conn.commit()

    def get_bulk_job(self, job_id: str) -> Optional[dict]:
        """Get bulk job by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM bulk_jobs WHERE id = ?
            """,
                (job_id,),
            )

            row = cursor.fetchone()

            if row:
                data = dict(row)

                # Parse JSON fields
                if data.get("extension_ids"):
                    try:
                        data["extension_ids"] = json.loads(data["extension_ids"])
                    except Exception:
                        data["extension_ids"] = []

                if data.get("stores"):
                    try:
                        data["stores"] = json.loads(data["stores"])
                    except Exception:
                        data["stores"] = []

                if data.get("results"):
                    try:
                        data["results"] = json.loads(data["results"])
                    except Exception:
                        data["results"] = None

                return data

        return None

    def cleanup_old_bulk_jobs(self, hours: int = 24) -> int:
        """Delete old completed/failed bulk jobs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

            cursor.execute(
                """
                DELETE FROM bulk_jobs
                WHERE status IN ('completed', 'failed') AND completed_at < ?
            """,
                (cutoff,),
            )

            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Cleaned up {deleted} old bulk jobs")
            return deleted
