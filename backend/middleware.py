"""
Middleware functions for Flask application
"""
import functools
import logging
from flask import request, jsonify, g
from datetime import datetime
from config import get_config

logger = logging.getLogger(__name__)


def require_api_key(f):
    """
    Decorator to require API key for certain endpoints
    
    Usage:
        @app.route('/api/endpoint')
        @require_api_key
        def endpoint():
            ...
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        config = get_config()
        
        if config.API_KEY_REQUIRED:
            api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                logger.warning(f"Missing API key from {request.remote_addr}")
                return jsonify({'error': 'API key required'}), 401
            
            if api_key != config.API_KEY:
                logger.warning(f"Invalid API key from {request.remote_addr}")
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Store validated API key in g for potential use
            g.api_key = api_key
        
        return f(*args, **kwargs)
    
    return decorated_function


def log_request(f):
    """
    Decorator to log API requests
    
    Usage:
        @app.route('/api/endpoint')
        @log_request
        def endpoint():
            ...
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request details
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
        
        # Store request start time
        g.request_start_time = datetime.now()
        
        # Process request
        response = f(*args, **kwargs)
        
        # Log response time
        if hasattr(g, 'request_start_time'):
            duration = (datetime.now() - g.request_start_time).total_seconds()
            logger.info(f"Response time: {duration:.3f}s")
        
        return response
    
    return decorated_function


def validate_json(f):
    """
    Decorator to validate JSON request body
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_json
        def endpoint():
            data = request.get_json()  # Guaranteed to be valid
            ...
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            try:
                request.get_json()
            except Exception as e:
                logger.error(f"Invalid JSON in request: {e}")
                return jsonify({'error': 'Invalid JSON in request body'}), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit_by_ip(max_requests=10, window_seconds=60):
    """
    Simple IP-based rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
    
    Usage:
        @app.route('/api/endpoint')
        @rate_limit_by_ip(max_requests=5, window_seconds=60)
        def endpoint():
            ...
    """
    # Simple in-memory storage (use Redis in production)
    request_counts = {}
    
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = datetime.now()
            
            # Clean old entries
            for ip in list(request_counts.keys()):
                if (current_time - request_counts[ip]['first_request']).total_seconds() > window_seconds:
                    del request_counts[ip]
            
            # Check rate limit
            if client_ip in request_counts:
                if request_counts[client_ip]['count'] >= max_requests:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window_seconds
                    }), 429
                request_counts[client_ip]['count'] += 1
            else:
                request_counts[client_ip] = {
                    'count': 1,
                    'first_request': current_time
                }
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def cors_headers(f):
    """
    Add CORS headers to response
    
    Usage:
        @app.route('/api/endpoint')
        @cors_headers
        def endpoint():
            ...
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add CORS headers
        if hasattr(response, 'headers'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
        
        return response
    
    return decorated_function


def sanitize_input(f):
    """
    Sanitize input data to prevent injection attacks
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @sanitize_input
        def endpoint():
            ...
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            data = request.get_json()
            
            # Basic sanitization - remove any HTML/script tags
            def sanitize_value(value):
                if isinstance(value, str):
                    # Remove potential HTML/script tags
                    import re
                    value = re.sub(r'<[^>]*>', '', value)
                    # Limit length
                    return value[:1000]
                elif isinstance(value, dict):
                    return {k: sanitize_value(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [sanitize_value(item) for item in value]
                return value
            
            # Store sanitized data
            g.sanitized_json = sanitize_value(data)
        
        return f(*args, **kwargs)
    
    return decorated_function
