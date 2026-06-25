"""
Simple in-process sliding-window rate limiter.
Keyed by user_id: max 20 requests per 60 seconds.

For production, replace with Redis + lua script for multi-instance safety.
"""

import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

WINDOW_SECONDS = 60
MAX_REQUESTS = 20


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit transaction writes
        if request.method == "POST" and request.url.path == "/transaction":
            # Try to extract user_id from body; if absent let validation handle it
            try:
                body = await request.json()
                user_id = body.get("user_id", "anonymous")
            except Exception:
                user_id = "anonymous"

            now = time.monotonic()
            window = self._windows[user_id]

            # Evict timestamps outside the window
            while window and window[0] < now - WINDOW_SECONDS:
                window.popleft()

            if len(window) >= MAX_REQUESTS:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: max {MAX_REQUESTS} transactions per {WINDOW_SECONDS}s per user.",
                )

            window.append(now)

            # Re-attach body for downstream handlers (body already consumed)
            import json
            body_bytes = json.dumps(body).encode()
            request._body = body_bytes

        return await call_next(request)