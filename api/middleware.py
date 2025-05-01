from functools import wraps
from flask import request, jsonify, g
import time
from utils.logger import Logger


class Middleware:
    @staticmethod
    def rate_limit(max_requests=100, window=60):
        """
        Rate limiting middleware
        max_requests: Maximum number of requests allowed in the time window
        window: Time window in seconds
        """

        def decorator(f):
            # Use a simple in-memory store for rate limiting
            # In production, you'd use Redis or a similar distributed cache
            request_counts = {}

            @wraps(f)
            def wrapped(*args, **kwargs):
                # Get client IP
                client_ip = request.remote_addr

                # Get current timestamp
                current_time = time.time()

                # Clean up old entries
                for ip in list(request_counts.keys()):
                    if current_time - request_counts[ip]['timestamp'] > window:
                        del request_counts[ip]

                # Check if IP exists in request_counts
                if client_ip in request_counts:
                    # Check if window has expired
                    if current_time - request_counts[client_ip]['timestamp'] > window:
                        # Reset counter
                        request_counts[client_ip] = {
                            'count': 1,
                            'timestamp': current_time
                        }
                    else:
                        # Increment counter
                        request_counts[client_ip]['count'] += 1

                        # Check if limit exceeded
                        if request_counts[client_ip]['count'] > max_requests:
                            Logger.log_security_event(
                                'rate_limit_exceeded',
                                {'ip': client_ip, 'path': request.path},
                                'warning'
                            )
                            return jsonify({
                                'message': 'Rate limit exceeded. Please try again later.'
                            }), 429
                else:
                    # Add new entry
                    request_counts[client_ip] = {
                        'count': 1,
                        'timestamp': current_time
                    }

                return f(*args, **kwargs)

            return wrapped

        return decorator

    @staticmethod
    def cors_headers(response):
        """Add CORS headers to response"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @staticmethod
    def options_handler():
        """Handle OPTIONS requests for CORS preflight"""
        response = jsonify({'message': 'OK'})
        return Middleware.cors_headers(response)

    @staticmethod
    def request_logger():
        """Log request details"""

        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                # Store start time
                g.start_time = time.time()

                # Process request
                response = f(*args, **kwargs)

                # Calculate response time
                response_time = (time.time() - g.start_time) * 1000  # Convert to milliseconds

                # Log request
                Logger.log_api_request(request, response.status_code, response_time)

                return response

            return wrapped

        return decorator
