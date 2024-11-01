# app/middleware.py

from functools import wraps
from flask import request, jsonify, current_app
import time
from http import HTTPStatus
from typing import Callable, Dict, Any
import threading
import logging

class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.clients: Dict[str, list] = {}
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        with self.lock:
            current_time = time.time()
            if client_id not in self.clients:
                self.clients[client_id] = []
            self.clients[client_id] = [
                req_time for req_time in self.clients[client_id]
                if current_time - req_time < self.window
            ]
            if len(self.clients[client_id]) >= self.requests:
                return False
            self.clients[client_id].append(current_time)
            return True

def setup_middleware(app):
    """Set up all middleware for the application."""
    
    @app.before_request
    def log_request_info():
        # Skip logging for static files
        if not request.path.startswith('/static/'):
            app.logger.debug('Headers: %s', request.headers)
            app.logger.debug('Body: %s', request.get_data())

    @app.after_request
    def log_response_info(response):
        # Skip logging for static files
        if not request.path.startswith('/static/'):
            # Only log response data for JSON responses
            if response.content_type == 'application/json':
                app.logger.debug('Response: %s', response.get_data().decode('utf-8'))
            else:
                app.logger.debug('Response: [Content-Type: %s]', response.content_type)
        return response

    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add CORS headers for API endpoints
        if request.path.startswith('/api/'):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response

    # Register error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        app.logger.error(f"Error: {str(error)}", exc_info=True)
        
        if hasattr(error, 'code') and error.code == 404:
            return jsonify({
                "error": "Not found",
                "message": str(error)
            }), 404
            
        return jsonify({
            "error": "Internal server error",
            "message": str(error)
        }), 500

    # Add rate limiter if enabled
    if app.config.get('ENABLE_RATE_LIMITING'):
        app.rate_limiter = RateLimiter(
            app.config.get('RATE_LIMIT_REQUESTS', 100),
            app.config.get('RATE_LIMIT_WINDOW', 3600)
        )