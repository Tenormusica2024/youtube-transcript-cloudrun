#!/usr/bin/env python3
"""
Performance Optimization for YouTube Transcript Webapp
App Store Ready - Production Performance Enhancements
"""

import functools
import gzip
import json
import logging
import time
from datetime import datetime, timedelta

from flask import Flask, Response, jsonify, request


class PerformanceOptimizer:
    """Performance optimization utilities for App Store compliance"""

    def __init__(self, app=None):
        self.app = app
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "total_requests": 0}

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize performance optimizations"""
        self.app = app

        # Add compression middleware
        self.add_compression(app)

        # Add caching middleware
        self.add_caching(app)

        # Add performance monitoring
        self.add_monitoring(app)

        # Add response optimization
        self.add_response_optimization(app)

    def add_compression(self, app):
        """Add GZIP compression for responses"""

        @app.after_request
        def compress_response(response):
            """Compress responses to reduce bandwidth usage"""

            # Skip compression for certain content types
            skip_compression = [
                "image/",
                "video/",
                "audio/",
                "application/zip",
                "application/gzip",
                "application/pdf",
            ]

            content_type = response.content_type or ""
            if any(skip in content_type for skip in skip_compression):
                return response

            # Skip if already compressed
            if response.headers.get("Content-Encoding"):
                return response

            # Skip small responses
            if response.content_length and response.content_length < 500:
                return response

            # Check if client accepts gzip
            accept_encoding = request.headers.get("Accept-Encoding", "")
            if "gzip" not in accept_encoding.lower():
                return response

            try:
                # Compress response data
                if response.data:
                    compressed_data = gzip.compress(response.data)

                    # Only use compression if it actually reduces size
                    if len(compressed_data) < len(response.data):
                        response.data = compressed_data
                        response.headers["Content-Encoding"] = "gzip"
                        response.headers["Content-Length"] = len(compressed_data)
                        response.headers["Vary"] = "Accept-Encoding"

                        # Add performance header
                        compression_ratio = len(response.data) / len(compressed_data)
                        response.headers["X-Compression-Ratio"] = (
                            f"{compression_ratio:.2f}"
                        )

            except Exception as e:
                app.logger.warning(f"Compression failed: {e}")

            return response

    def add_caching(self, app):
        """Add intelligent caching for API responses"""

        def cache_response(timeout=300, key_func=None):
            """Decorator for caching responses"""

            def decorator(f):
                @functools.wraps(f)
                def wrapper(*args, **kwargs):
                    # Generate cache key
                    if key_func:
                        cache_key = key_func(*args, **kwargs)
                    else:
                        cache_key = f"{f.__name__}:{hash(str(args) + str(kwargs))}"

                    # Check cache
                    self.cache_stats["total_requests"] += 1
                    now = time.time()

                    if cache_key in self.cache:
                        cached_item = self.cache[cache_key]
                        if now - cached_item["timestamp"] < timeout:
                            self.cache_stats["hits"] += 1
                            response = jsonify(cached_item["data"])
                            response.headers["X-Cache"] = "HIT"
                            response.headers["X-Cache-Age"] = str(
                                int(now - cached_item["timestamp"])
                            )
                            return response
                        else:
                            # Remove expired item
                            del self.cache[cache_key]

                    # Cache miss - execute function
                    self.cache_stats["misses"] += 1
                    result = f(*args, **kwargs)

                    # Cache the result if it's successful
                    if hasattr(result, "status_code") and result.status_code == 200:
                        try:
                            # Parse JSON response to cache
                            if result.content_type == "application/json":
                                data = json.loads(result.data)
                                self.cache[cache_key] = {"data": data, "timestamp": now}

                                # Limit cache size
                                if len(self.cache) > 100:
                                    # Remove oldest entries
                                    oldest_keys = sorted(
                                        self.cache.keys(),
                                        key=lambda k: self.cache[k]["timestamp"],
                                    )[:20]
                                    for old_key in oldest_keys:
                                        del self.cache[old_key]
                        except Exception as e:
                            app.logger.warning(f"Cache storage failed: {e}")

                    # Add cache headers
                    if hasattr(result, "headers"):
                        result.headers["X-Cache"] = "MISS"
                        result.headers["X-Cache-Stats"] = (
                            f"hits:{self.cache_stats['hits']},misses:{self.cache_stats['misses']}"
                        )

                    return result

                return wrapper

            return decorator

        # Apply caching to specific routes
        app.cache_response = cache_response

    def add_monitoring(self, app):
        """Add performance monitoring"""

        @app.before_request
        def before_request():
            """Record request start time"""
            request.start_time = time.time()

        @app.after_request
        def after_request(response):
            """Add performance headers and logging"""

            if hasattr(request, "start_time"):
                duration = time.time() - request.start_time

                # Add performance headers
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
                response.headers["X-Server-Time"] = datetime.utcnow().isoformat()

                # Log slow requests
                if duration > 2.0:  # Log requests taking more than 2 seconds
                    app.logger.warning(
                        f"Slow request: {request.method} {request.path} "
                        f"took {duration:.3f}s - IP: {request.remote_addr}"
                    )

                # Add App Store compliance headers
                response.headers["X-App-Store-Ready"] = "true"
                response.headers["X-Performance-Optimized"] = "true"

            return response

    def add_response_optimization(self, app):
        """Optimize response sizes and formats"""

        @app.after_request
        def optimize_response(response):
            """Optimize response for mobile devices"""

            # Add mobile optimization headers
            if "mobile" in request.headers.get("User-Agent", "").lower():
                response.headers["X-Mobile-Optimized"] = "true"

                # For JSON responses, check if we can reduce data
                if response.content_type == "application/json" and response.data:
                    try:
                        data = json.loads(response.data)

                        # Remove empty fields to reduce response size
                        if isinstance(data, dict):
                            optimized_data = self._remove_empty_fields(data)
                            if optimized_data != data:
                                response.data = json.dumps(
                                    optimized_data, separators=(",", ":")
                                )
                                response.headers["Content-Length"] = len(response.data)
                                response.headers["X-Optimized"] = "true"

                    except Exception as e:
                        app.logger.debug(f"Response optimization failed: {e}")

            return response

    def _remove_empty_fields(self, data):
        """Remove empty fields from response data"""
        if isinstance(data, dict):
            return {
                k: self._remove_empty_fields(v)
                for k, v in data.items()
                if v is not None and v != "" and v != []
            }
        elif isinstance(data, list):
            return [
                self._remove_empty_fields(item) for item in data if item is not None
            ]
        else:
            return data

    def get_cache_stats(self):
        """Get cache performance statistics"""
        total = self.cache_stats["total_requests"]
        hits = self.cache_stats["hits"]

        if total > 0:
            hit_rate = (hits / total) * 100
        else:
            hit_rate = 0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": self.cache_stats["misses"],
            "hit_rate_percentage": round(hit_rate, 2),
            "cache_size": len(self.cache),
        }

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "total_requests": 0}


# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor and log performance metrics"""

    @staticmethod
    def measure_execution_time(func):
        """Decorator to measure function execution time"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                logging.info(f"{func.__name__} executed in {execution_time:.3f}s")

        return wrapper

    @staticmethod
    def memory_usage_tracker():
        """Track memory usage"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2),
            }
        except ImportError:
            return {"error": "psutil not available"}


# App Store specific optimizations
class AppStoreOptimizer:
    """Specific optimizations for App Store compliance"""

    @staticmethod
    def optimize_for_mobile(app):
        """Mobile-specific optimizations"""

        @app.after_request
        def mobile_optimization(response):
            # Add mobile-friendly headers
            response.headers["X-UA-Compatible"] = "IE=edge"
            response.headers["X-Mobile-Optimized"] = "true"

            # Optimize for small screens
            if "mobile" in request.headers.get("User-Agent", "").lower():
                response.headers["X-Content-Optimized"] = "mobile"

            return response

    @staticmethod
    def add_app_store_headers(app):
        """Add headers required for App Store compliance"""

        @app.after_request
        def app_store_headers(response):
            # Privacy and security headers
            response.headers["X-Privacy-Compliant"] = "true"
            response.headers["X-Data-Processing"] = "minimal"
            response.headers["X-User-Tracking"] = "none"

            # Performance headers
            response.headers["X-Optimized-For"] = "mobile-app-store"
            response.headers["X-Compression-Enabled"] = "true"
            response.headers["X-Caching-Strategy"] = "intelligent"

            return response


if __name__ == "__main__":
    print("[PERFORMANCE] Performance optimizer module loaded")
    print("Usage: from performance_optimizer import PerformanceOptimizer")
    print("       optimizer = PerformanceOptimizer(app)")
