"""
Performance optimization utilities for App Store compliance
"""

import gzip
import functools
from flask import make_response, request
import json


class PerformanceOptimizer:
    """Flask app performance optimization"""
    
    def __init__(self, app):
        self.app = app
        self.setup_compression()
        self.setup_caching()
    
    def setup_compression(self):
        """Enable response compression"""
        @self.app.after_request
        def compress_response(response):
            if not request.path.startswith('/static'):
                return response
            
            response.direct_passthrough = False
            
            if (response.status_code < 200 or 
                response.status_code >= 300 or 
                'Content-Encoding' in response.headers):
                return response
            
            response.headers['Content-Encoding'] = 'gzip'
            response.data = gzip.compress(response.data)
            response.headers['Content-Length'] = len(response.data)
            
            return response
    
    def setup_caching(self):
        """Setup caching headers"""
        @self.app.after_request
        def add_cache_headers(response):
            if request.path.startswith('/static'):
                response.headers['Cache-Control'] = 'public, max-age=31536000'
            elif request.path.startswith('/api'):
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response


class AppStoreOptimizer:
    """App Store specific optimizations"""
    
    @staticmethod
    def optimize_for_mobile(app):
        """Mobile-specific optimizations"""
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
        app.config['TEMPLATES_AUTO_RELOAD'] = False
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
    @staticmethod
    def add_app_store_headers(app):
        """Add App Store required headers"""
        @app.after_request
        def add_headers(response):
            response.headers['X-App-Store-Compatible'] = '2.0.0'
            response.headers['X-Mobile-Optimized'] = 'true'
            return response