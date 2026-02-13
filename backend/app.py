"""
Flask API for Browser Extension OSINT Tool
"""
import os
import logging
import uuid
import threading
import hmac
import functools
import time
import json
from datetime import datetime
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from urllib.parse import quote as requests_quote
from werkzeug.middleware.proxy_fix import ProxyFix

# Import components
from database.manager import DatabaseManager
from scrapers.chrome import ChromeStoreScraper
from scrapers.firefox import FirefoxAddonsScraper
from scrapers.edge import EdgeAddonsScraper
from scrapers.safari import SafariExtensionScraper
from services.bulk_executor import BulkSearchExecutor
from services.blocklist_manager import BlocklistManager
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Apply ProxyFix for proper client IP detection behind reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Sanitized config logging
logger.info(f"API key authentication: {'enabled' if config.API_KEY_REQUIRED else 'disabled'}")

# Initialize CORS
CORS(app, origins=config.CORS_ORIGINS)

# Initialize rate limiter with Redis storage if available
if config.REDIS_URL:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=config.REDIS_URL,
        default_limits=["100 per hour"],
    )
else:
    limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["100 per hour"])

# Initialize cache
cache = Cache(app, config={"CACHE_TYPE": "simple"})

# Initialize database manager
db_manager = DatabaseManager()

# Initialize scrapers
scrapers = {
    "chrome": ChromeStoreScraper(),
    "firefox": FirefoxAddonsScraper(),
    "edge": EdgeAddonsScraper(),
    "safari": SafariExtensionScraper(),
}

# Scraper classes for bulk executor (need fresh instances per thread)
SCRAPER_CLASSES = {
    "chrome": ChromeStoreScraper,
    "firefox": FirefoxAddonsScraper,
    "edge": EdgeAddonsScraper,
    "safari": SafariExtensionScraper,
}

# Active bulk jobs
active_jobs = {}  # job_id -> BulkSearchExecutor
MAX_ACTIVE_JOBS = 100

# Initialize blocklist manager
blocklist_manager = BlocklistManager()


# Refresh blocklists in background thread on startup
def _init_blocklists():
    try:
        blocklist_manager.refresh_blocklists()
    except Exception as e:
        logger.error(f"Initial blocklist refresh failed: {e}")


threading.Thread(target=_init_blocklists, daemon=True).start()


def cleanup_completed_jobs():
    """Remove completed jobs from active_jobs to prevent memory exhaustion."""
    completed = []
    for jid in list(active_jobs.keys()):
        job = db_manager.get_bulk_job(jid)
        if job and job["status"] in ["completed", "failed", "cancelled"]:
            completed.append(jid)
    for jid in completed:
        del active_jobs[jid]


# API key validation decorator
def require_api_key(f):
    """Decorator to require API key for protected endpoints"""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check app.config first for testability, then fall back to env var
        api_key_required = app.config.get("API_KEY_REQUIRED", False)
        if isinstance(api_key_required, str):
            api_key_required = api_key_required.lower() == "true"
        # Also check env var (allows runtime override and test monkeypatching)
        if not api_key_required:
            api_key_required = os.environ.get("API_KEY_REQUIRED", "False").lower() == "true"

        if not api_key_required:
            return f(*args, **kwargs)

        # Only accept API key via header (not query parameter)
        api_key = request.headers.get("X-API-Key")

        # Use timing-safe comparison to prevent timing attacks
        expected_key = app.config.get("API_KEY", config.API_KEY)
        if not api_key or not hmac.compare_digest(api_key, expected_key):
            return jsonify({"error": "Invalid or missing API key"}), 401

        return f(*args, **kwargs)

    return decorated_function


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "version": config.VERSION,
            "database": os.path.exists(config.DATABASE_PATH),
        }
    )


@app.route("/api/search", methods=["POST"])
@limiter.limit("30 per minute")
@require_api_key
def search_extension():
    """Search for a browser extension"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    extension_id = data.get("extension_id", "").strip()
    stores = data.get("stores", ["chrome", "firefox", "edge"])
    include_permissions = data.get("include_permissions", False)

    if not extension_id:
        return jsonify({"error": "Extension ID is required"}), 400

    if len(extension_id) > 256:
        return jsonify({"error": "Extension ID too long"}), 400

    # Log the search
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent", "")

    results = []
    found_stores = []

    # Search all requested stores - let each scraper handle validation
    stores_to_search = [s for s in stores if s in scrapers]

    for store in stores_to_search:
        # Check cache first
        cached_data = db_manager.get_from_cache(extension_id, store)

        if cached_data:
            # Only include if it was actually found
            if cached_data.found:
                cached_data.cached = True
                results.append(cached_data.to_dict())
                found_stores.append(store)
            else:
                # Cache shows not found - check if it was previously found (delisted)
                previous_cache = db_manager.get_previous_found_entry(extension_id, store)
                if previous_cache:
                    result_dict = previous_cache.to_dict()
                    result_dict["delisted"] = True
                    result_dict["cached"] = True
                    results.append(result_dict)
                    logger.info(f"Extension {extension_id} marked as delisted in {store}")
            logger.info(f"Cache hit for {extension_id} in {store} (found: {cached_data.found})")
        else:
            # Scrape if not in cache
            try:
                scraper = scrapers[store]
                # Pass include_permissions only to Chrome scraper
                if store == "chrome":
                    extension_data = scraper.scrape(
                        extension_id, include_permissions=include_permissions
                    )
                else:
                    extension_data = scraper.scrape(extension_id)

                if extension_data:
                    # Check for delisted BEFORE saving (save overwrites old entry)
                    previous_cache = None
                    if not extension_data.found:
                        previous_cache = db_manager.get_previous_found_entry(extension_id, store)

                    # Save to cache regardless of found status
                    db_manager.save_to_cache(extension_data)
                    # Only include in results if actually found
                    if extension_data.found:
                        results.append(extension_data.to_dict())
                        found_stores.append(store)
                    elif previous_cache:
                        # Extension was previously found but now gone = delisted
                        result_dict = previous_cache.to_dict()
                        result_dict["delisted"] = True
                        result_dict["cached"] = True
                        results.append(result_dict)
                        logger.info(f"Extension {extension_id} marked as delisted in {store}")
                    logger.info(
                        f"Scraped {extension_id} from {store} (found: {extension_data.found})"
                    )
            except Exception as e:
                logger.error(f"Error scraping {store} for {extension_id}: {e}")
                # Don't include error results in the response

    # Check blocklists for this extension
    blocklist_matches = blocklist_manager.check_extension(extension_id)
    if blocklist_matches:
        if results:
            for result in results:
                result["blocklist_matches"] = blocklist_matches
        else:
            # Extension not found in any store but is on a blocklist —
            # create a minimal result so the warning is still shown
            blocklist_name = blocklist_matches[0].get("name")
            results.append(
                {
                    "extension_id": extension_id,
                    "name": blocklist_name or extension_id,
                    "found": False,
                    "store_source": stores_to_search[0] if stores_to_search else "unknown",
                    "blocklist_matches": blocklist_matches,
                    "permissions": [],
                    "cached": False,
                }
            )

    # Log the search
    db_manager.log_search(extension_id, found_stores, ip_address, user_agent)

    return jsonify({"extension_id": extension_id, "results": results})


@app.route("/api/bulk-search", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def bulk_search_extensions():
    """Bulk search for multiple extensions"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    extension_ids = data.get("extension_ids", [])
    stores = data.get("stores", ["chrome", "firefox", "edge"])
    include_permissions = data.get("include_permissions", False)

    # Validate extension_ids is an array
    if not isinstance(extension_ids, list):
        return jsonify({"error": "extension_ids must be an array"}), 400

    # Strip and filter extension IDs
    extension_ids = [
        str(eid).strip()
        for eid in extension_ids
        if isinstance(eid, str) and len(str(eid).strip()) > 0
    ]

    if not extension_ids:
        return jsonify({"error": "Extension IDs are required"}), 400

    if any(len(eid) > 256 for eid in extension_ids):
        return jsonify({"error": "Extension ID too long (max 256 chars)"}), 400

    if len(extension_ids) > 50:
        return jsonify({"error": "Maximum 50 extensions per bulk search"}), 400

    results = {}

    for ext_id in extension_ids:
        ext_id = ext_id.strip()
        if not ext_id:
            continue

        ext_results = []

        # Search all requested stores for this ID
        stores_to_search = [s for s in stores if s in scrapers]

        for store in stores_to_search:
            # Check cache first
            cached_data = db_manager.get_from_cache(ext_id, store)

            if cached_data:
                if cached_data.found:
                    cached_data.cached = True
                    ext_results.append(cached_data.to_dict())
                else:
                    # Cache shows not found - check if it was previously found (delisted)
                    previous_cache = db_manager.get_previous_found_entry(ext_id, store)
                    if previous_cache:
                        result_dict = previous_cache.to_dict()
                        result_dict["delisted"] = True
                        result_dict["cached"] = True
                        ext_results.append(result_dict)
                        logger.info(f"Extension {ext_id} marked as delisted in {store}")
            else:
                # Scrape if not in cache
                try:
                    scraper = scrapers[store]
                    # Pass include_permissions only to Chrome scraper
                    if store == "chrome":
                        extension_data = scraper.scrape(
                            ext_id, include_permissions=include_permissions
                        )
                    else:
                        extension_data = scraper.scrape(ext_id)

                    if extension_data:
                        # Check for delisted BEFORE saving (save overwrites old entry)
                        previous_cache = None
                        if not extension_data.found:
                            previous_cache = db_manager.get_previous_found_entry(ext_id, store)

                        db_manager.save_to_cache(extension_data)
                        if extension_data.found:
                            ext_results.append(extension_data.to_dict())
                        elif previous_cache:
                            # Extension was previously found but now gone = delisted
                            result_dict = previous_cache.to_dict()
                            result_dict["delisted"] = True
                            result_dict["cached"] = True
                            ext_results.append(result_dict)
                            logger.info(f"Extension {ext_id} marked as delisted in {store}")
                except Exception as e:
                    logger.error(f"Error in bulk search for {ext_id} in {store}: {e}")

        # Check blocklists
        blocklist_matches = blocklist_manager.check_extension(ext_id)
        if blocklist_matches:
            if ext_results:
                for result in ext_results:
                    result["blocklist_matches"] = blocklist_matches
            else:
                blocklist_name = blocklist_matches[0].get("name")
                ext_results.append(
                    {
                        "extension_id": ext_id,
                        "name": blocklist_name or ext_id,
                        "found": False,
                        "store_source": stores_to_search[0] if stores_to_search else "unknown",
                        "blocklist_matches": blocklist_matches,
                        "permissions": [],
                        "cached": False,
                    }
                )

        results[ext_id] = ext_results

    return jsonify({"results": results})


@app.route("/api/search-by-name", methods=["POST"])
@limiter.limit("20 per minute")
@require_api_key
def search_by_name():
    """Search for extensions by name across stores"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    name = data.get("name", "").strip()
    exclude_stores = data.get("exclude_stores", [])

    # Validate and parse limit with error handling
    try:
        limit = min(int(data.get("limit", 5)), 10)
        if limit < 1:
            limit = 1
    except (TypeError, ValueError):
        limit = 5

    if not name:
        return jsonify({"error": "Extension name is required"}), 400

    if len(name) > 200:
        return jsonify({"error": "Search name too long (max 200 characters)"}), 400

    results = {}
    search_urls = {}

    for store_name, scraper in scrapers.items():
        if store_name in exclude_stores:
            continue

        # Get search results from stores that support it
        matches = scraper.search_by_name(name, limit=limit)
        results[store_name] = [m.to_dict() for m in matches]

        # Always provide a manual search URL
        if store_name == "chrome":
            search_urls[
                store_name
            ] = f"https://chromewebstore.google.com/search/{requests_quote(name)}"
        elif store_name == "firefox":
            search_urls[
                store_name
            ] = f"https://addons.mozilla.org/en-US/firefox/search/?q={requests_quote(name)}"
        elif store_name == "edge":
            search_urls[
                store_name
            ] = f"https://microsoftedge.microsoft.com/addons/search/{requests_quote(name)}"
        elif store_name == "safari":
            search_urls[
                store_name
            ] = f"https://apps.apple.com/us/search?term={requests_quote(name)}"

    return jsonify(
        {
            "name": name,
            "results": results,
            "search_urls": search_urls,
        }
    )


@app.route("/api/stats", methods=["GET"])
@require_api_key
def get_statistics():
    """Get cache and usage statistics"""
    try:
        stats = db_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500


@app.route("/api/cleanup", methods=["POST"])
@limiter.limit("1 per hour")
@require_api_key
def cleanup_cache():
    """Clean up old cache entries"""
    data = request.get_json() or {}
    days = data.get("days", config.DATABASE_CACHE_EXPIRY_DAYS * 2)

    # Validate days parameter
    try:
        days = int(days)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid 'days' parameter"}), 400

    if days < 1 or days > 365:
        return jsonify({"error": "'days' must be between 1 and 365"}), 400

    try:
        deleted = db_manager.cleanup_old_cache(days)
        history_deleted = db_manager.cleanup_old_search_history(days)
        message = (
            f"Cleaned up {deleted} old cache entries and "
            f"{history_deleted} search history entries"
        )
        return jsonify(
            {"message": message, "cache_deleted": deleted, "history_deleted": history_deleted}
        )
    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")
        return jsonify({"error": "Failed to clean cache"}), 500


@app.route("/api/extension/<extension_id>/history", methods=["GET"])
@limiter.limit("30 per minute")
@require_api_key
def get_extension_history(extension_id):
    """Get historical snapshots for an extension"""
    # Get store query parameter
    store = request.args.get("store", "").strip().lower()

    # Validate store parameter
    if not store:
        return jsonify({"error": "Store parameter is required"}), 400

    if store not in ["chrome", "firefox", "edge", "safari"]:
        return (
            jsonify({"error": "Invalid store. Must be one of: chrome, firefox, edge, safari"}),
            400,
        )

    try:
        # Get historical snapshots
        snapshots = db_manager.get_extension_history(extension_id, store)

        # Compute diffs between consecutive snapshots
        enhanced_snapshots = []
        for i, snapshot in enumerate(snapshots):
            enhanced_snapshot = {
                "version": snapshot["version"],
                "name": snapshot["name"],
                "permissions": snapshot["permissions"],
                "scraped_at": snapshot["scraped_at"],
            }

            if i == 0:
                # First snapshot has no diff
                enhanced_snapshot["diff"] = None
            else:
                # Compare with previous snapshot
                prev_snapshot = snapshots[i - 1]

                prev_permissions_set = set(prev_snapshot["permissions"])
                curr_permissions_set = set(snapshot["permissions"])

                added = sorted(list(curr_permissions_set - prev_permissions_set))
                removed = sorted(list(prev_permissions_set - curr_permissions_set))

                version_changed = snapshot["version"] != prev_snapshot["version"]
                name_changed = snapshot["name"] != prev_snapshot["name"]

                enhanced_snapshot["diff"] = {
                    "added": added,
                    "removed": removed,
                    "version_changed": version_changed,
                    "previous_version": (prev_snapshot["version"] if version_changed else None),
                    "name_changed": name_changed,
                    "previous_name": (prev_snapshot["name"] if name_changed else None),
                }

            enhanced_snapshots.append(enhanced_snapshot)

        # Determine if there are any permission changes
        has_permission_changes = any(
            snap["diff"] and (snap["diff"]["added"] or snap["diff"]["removed"])
            for snap in enhanced_snapshots
        )

        return jsonify(
            {
                "extension_id": extension_id,
                "store": store,
                "snapshots": enhanced_snapshots,
                "total_snapshots": len(enhanced_snapshots),
                "has_permission_changes": has_permission_changes,
            }
        )

    except Exception as e:
        logger.error(f"Error getting extension history: {e}")
        return jsonify({"error": "Failed to retrieve extension history"}), 500


@app.route("/api/bulk-search-async", methods=["POST"])
@limiter.limit("5 per minute")
@require_api_key
def bulk_search_async():
    """Submit a bulk search job for async processing"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    extension_ids = data.get("extension_ids", [])
    stores = data.get("stores", ["chrome", "firefox", "edge"])
    include_permissions = data.get("include_permissions", False)

    # Validate extension_ids is an array
    if not isinstance(extension_ids, list):
        return jsonify({"error": "extension_ids must be an array"}), 400

    # Strip and filter extension IDs
    extension_ids = [
        str(eid).strip()
        for eid in extension_ids
        if isinstance(eid, str) and len(str(eid).strip()) > 0
    ]

    if not extension_ids:
        return jsonify({"error": "Extension IDs are required"}), 400

    if any(len(eid) > 256 for eid in extension_ids):
        return jsonify({"error": "Extension ID too long (max 256 chars)"}), 400

    if len(extension_ids) > 50:
        return jsonify({"error": "Maximum 50 extensions per bulk search"}), 400

    # Validate stores
    valid_stores = [s for s in stores if s in SCRAPER_CLASSES]
    if not valid_stores:
        return jsonify({"error": "No valid stores specified"}), 400

    # Clean up completed jobs and check capacity
    cleanup_completed_jobs()
    if len(active_jobs) >= MAX_ACTIVE_JOBS:
        return jsonify({"error": "Too many active jobs. Try again later."}), 429

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Calculate total tasks
    total_tasks = len(extension_ids) * len(valid_stores)

    # Create job in database
    db_manager.create_bulk_job(
        job_id=job_id,
        api_key_id=None,  # Could track API key if needed
        extension_ids=extension_ids,
        stores=valid_stores,
        include_permissions=include_permissions,
        total_tasks=total_tasks,
    )

    # Create executor
    executor = BulkSearchExecutor(
        db_manager=db_manager,
        scraper_classes=SCRAPER_CLASSES,
        max_workers=config.BULK_MAX_WORKERS,
    )

    # Store executor
    active_jobs[job_id] = executor

    # Start execution in background thread
    thread = threading.Thread(
        target=executor.execute,
        args=(job_id, extension_ids, valid_stores, include_permissions),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started bulk job {job_id} with {total_tasks} tasks")

    return (
        jsonify(
            {
                "job_id": job_id,
                "status": "pending",
                "total_tasks": total_tasks,
                "poll_url": f"/api/bulk-search-async/{job_id}",
                "stream_url": f"/api/bulk-search-async/{job_id}/stream",
            }
        ),
        202,
    )


@app.route("/api/bulk-search-async/<job_id>", methods=["GET"])
@limiter.limit("60 per minute")
def get_bulk_job_status(job_id):
    """Get status of a bulk search job"""
    job = db_manager.get_bulk_job(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Calculate progress percentage
    progress_pct = 0
    if job["total_tasks"] > 0:
        progress_pct = round((job["completed_tasks"] / job["total_tasks"]) * 100, 2)

    # Calculate elapsed time
    elapsed_seconds = None
    if job["started_at"]:
        started = datetime.fromisoformat(job["started_at"])
        if job["completed_at"]:
            completed = datetime.fromisoformat(job["completed_at"])
            elapsed_seconds = (completed - started).total_seconds()
        else:
            elapsed_seconds = (datetime.now() - started).total_seconds()

    return jsonify(
        {
            "job_id": job["id"],
            "status": job["status"],
            "total_tasks": job["total_tasks"],
            "completed_tasks": job["completed_tasks"],
            "failed_tasks": job["failed_tasks"],
            "progress_pct": progress_pct,
            "results": job["results"],
            "error_message": job.get("error_message"),
            "started_at": job["started_at"],
            "completed_at": job.get("completed_at"),
            "elapsed_seconds": elapsed_seconds,
        }
    )


@app.route("/api/bulk-search-async/<job_id>/stream", methods=["GET"])
def stream_bulk_job(job_id):
    """Stream progress updates via Server-Sent Events"""
    # Check if job exists
    job = db_manager.get_bulk_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Get executor for this job
    executor = active_jobs.get(job_id)
    if not executor:
        # Job exists but no executor - might be completed or old
        return jsonify({"error": "Job stream not available"}), 410

    def generate():
        """Generate SSE events from result queue"""
        start_time = time.time()
        MAX_STREAM_SECONDS = 600  # 10 minutes

        try:
            while True:
                # Check for stream timeout
                if time.time() - start_time > MAX_STREAM_SECONDS:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Stream timeout'})}\n\n"
                    break

                try:
                    # Wait for events with timeout
                    event = executor.result_queue.get(timeout=1)

                    if event["type"] == "progress":
                        # Progress event
                        yield "event: progress\n"
                        yield f"data: {jsonify(event).get_data(as_text=True)}\n\n"

                    elif event["type"] == "error":
                        # Error event
                        yield "event: error\n"
                        yield f"data: {jsonify(event).get_data(as_text=True)}\n\n"

                    elif event["type"] == "complete":
                        # Completion event
                        yield "event: complete\n"
                        yield f"data: {jsonify(event).get_data(as_text=True)}\n\n"
                        break

                except Exception:
                    # Timeout or other error - check job status
                    current_job = db_manager.get_bulk_job(job_id)
                    if current_job and current_job["status"] in [
                        "completed",
                        "failed",
                        "cancelled",
                    ]:
                        # Job finished
                        yield "event: complete\n"
                        status_json = jsonify({"status": current_job["status"]})
                        yield f"data: {status_json.get_data(as_text=True)}\n\n"
                        break

        except GeneratorExit:
            logger.info(f"SSE stream closed for job {job_id}")

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.route("/api/bulk-search-async/<job_id>", methods=["DELETE"])
def cancel_bulk_job(job_id):
    """Cancel a running bulk search job"""
    job = db_manager.get_bulk_job(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job["status"] in ["completed", "failed", "cancelled"]:
        return (
            jsonify(
                {
                    "error": f"Job already {job['status']}",
                    "status": job["status"],
                }
            ),
            400,
        )

    # Get executor and set cancel flag
    executor = active_jobs.get(job_id)
    if executor:
        executor.cancel()

    # Update job status
    db_manager.update_bulk_job(job_id, status="cancelled")

    logger.info(f"Cancelled bulk job {job_id}")

    return jsonify({"job_id": job_id, "status": "cancelled"})


@app.route("/api/blocklist/status", methods=["GET"])
def blocklist_status():
    """Get blocklist service status"""
    status = blocklist_manager.get_status()
    return jsonify(status)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit errors"""
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error("Internal server error: %s", error)
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
