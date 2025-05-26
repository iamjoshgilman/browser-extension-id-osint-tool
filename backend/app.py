"""
Flask API for Browser Extension OSINT Tool
"""
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# Import components
from database.manager import DatabaseManager
from scrapers.chrome import ChromeStoreScraper
from scrapers.firefox import FirefoxAddonsScraper
from scrapers.edge import EdgeAddonsScraper
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Debug: Print config values
logger.info(f"API_KEY_REQUIRED from env: {os.environ.get('API_KEY_REQUIRED')}")
logger.info(f"API_KEY_REQUIRED in config: {config.API_KEY_REQUIRED}")

# Initialize CORS
CORS(app, origins=config.CORS_ORIGINS)

# Initialize rate limiter with Redis storage if available
if config.REDIS_URL:
    from flask_limiter.storage import RedisStorage
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=config.REDIS_URL,
        default_limits=["100 per hour"]
    )
else:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per hour"]
    )

# Initialize cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Initialize database manager
db_manager = DatabaseManager()

# Initialize scrapers
scrapers = {
    'chrome': ChromeStoreScraper(),
    'firefox': FirefoxAddonsScraper(),
    'edge': EdgeAddonsScraper()
}

# API key validation decorator
def require_api_key(f):
    """Decorator to require API key for protected endpoints"""
    def decorated_function(*args, **kwargs):
        # Check the environment variable directly each time
        api_key_required = os.environ.get('API_KEY_REQUIRED', 'False').lower() == 'true'
        
        if not api_key_required:
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key or api_key != config.API_KEY:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        
        return f(*args, **kwargs)
    
    # IMPORTANT: Set a unique name for the decorated function
    decorated_function.__name__ = f'api_key_{f.__name__}'
    return decorated_function

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': config.VERSION,
        'database': os.path.exists(config.DATABASE_PATH)
    })

@app.route('/api/search', methods=['POST'])
@limiter.limit("30 per minute")
@require_api_key
def search_extension():
    """Search for a browser extension"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    extension_id = data.get('extension_id', '').strip()
    stores = data.get('stores', ['chrome', 'firefox', 'edge'])
    
    if not extension_id:
        return jsonify({'error': 'Extension ID is required'}), 400
    
    # Log the search
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    results = []
    found_stores = []
    
    for store in stores:
        if store not in scrapers:
            continue
        
        # Check cache first
        cached_data = db_manager.get_from_cache(extension_id, store)
        
        if cached_data:
            cached_data.cached = True
            results.append(cached_data.to_dict())
            if cached_data.found:
                found_stores.append(store)
            logger.info(f"Cache hit for {extension_id} in {store}")
        else:
            # Scrape if not in cache
            try:
                scraper = scrapers[store]
                extension_data = scraper.scrape(extension_id)
                
                if extension_data:
                    db_manager.save_to_cache(extension_data)
                    results.append(extension_data.to_dict())
                    if extension_data.found:
                        found_stores.append(store)
                    logger.info(f"Scraped {extension_id} from {store}")
            except Exception as e:
                logger.error(f"Error scraping {store} for {extension_id}: {e}")
                results.append({
                    'extension_id': extension_id,
                    'store_source': store,
                    'found': False,
                    'error': str(e)
                })
    
    # Log the search
    db_manager.log_search(extension_id, found_stores, ip_address, user_agent)
    
    return jsonify({
        'extension_id': extension_id,
        'results': results
    })

@app.route('/api/bulk-search', methods=['POST'])
@limiter.limit("10 per minute")
@require_api_key
def bulk_search_extensions():
    """Bulk search for multiple extensions"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
    
    extension_ids = data.get('extension_ids', [])
    stores = data.get('stores', ['chrome', 'firefox', 'edge'])
    
    if not extension_ids:
        return jsonify({'error': 'Extension IDs are required'}), 400
    
    if len(extension_ids) > 50:
        return jsonify({'error': 'Maximum 50 extensions per bulk search'}), 400
    
    results = {}
    
    for ext_id in extension_ids:
        ext_id = ext_id.strip()
        if not ext_id:
            continue
        
        ext_results = []
        
        for store in stores:
            if store not in scrapers:
                continue
            
            # Check cache first
            cached_data = db_manager.get_from_cache(ext_id, store)
            
            if cached_data:
                cached_data.cached = True
                ext_results.append(cached_data.to_dict())
            else:
                # Scrape if not in cache
                try:
                    scraper = scrapers[store]
                    extension_data = scraper.scrape(ext_id)
                    
                    if extension_data:
                        db_manager.save_to_cache(extension_data)
                        ext_results.append(extension_data.to_dict())
                except Exception as e:
                    logger.error(f"Error in bulk search for {ext_id} in {store}: {e}")
        
        results[ext_id] = ext_results
    
    return jsonify({'results': results})

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_statistics():
    """Get cache and usage statistics"""
    try:
        stats = db_manager.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@app.route('/api/cleanup', methods=['POST'])
@limiter.limit("1 per hour")
@require_api_key
def cleanup_cache():
    """Clean up old cache entries"""
    data = request.get_json() or {}
    days = data.get('days', config.DATABASE_CACHE_EXPIRY_DAYS * 2)
    
    try:
        deleted = db_manager.cleanup_old_cache(days)
        return jsonify({
            'message': f'Cleaned up {deleted} old cache entries',
            'deleted': deleted
        })
    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")
        return jsonify({'error': 'Failed to clean cache'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': str(error)
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )
