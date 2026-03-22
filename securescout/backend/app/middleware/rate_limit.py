"""
Rate Limiting Middleware — enforces per-user scan limits via plan checks.
Global IP-based rate limiting is handled by SlowAPI in main.py.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple middleware placeholder. 
    Actual scan-level rate limiting is enforced inside ScanService.check_scan_limit().
    This middleware can be extended for IP-based blocking or abuse detection.
    """

    async def dispatch(self, request: Request, call_next):
        # Future: add Redis-based IP rate limiting here
        response = await call_next(request)
        return response
