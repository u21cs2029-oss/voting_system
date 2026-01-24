# gunicorn_config.py
"""
Gunicorn configuration for production deployment
"""

# Worker timeout (increase from default 30s to 120s)
timeout = 120

# Number of worker processes
workers = 2

# Worker class
worker_class = 'sync'

# Maximum requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Keep-alive connections
keepalive = 5