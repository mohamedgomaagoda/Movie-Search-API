from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from ..config import get_settings
from typing import Dict, Tuple
import asyncio

class RateLimiter:
    def __init__(self):
        self.settings = get_settings()
        self.requests: Dict[str, Tuple[int, float]] = {}  # IP: (count, start_time)
        self._cleanup_task = None

    async def cleanup(self):
        while True:
            current_time = time.time()
            # Remove entries older than 1 minute
            self.requests = {
                ip: (count, start_time)
                for ip, (count, start_time) in self.requests.items()
                if current_time - start_time < 60
            }
            await asyncio.sleep(60)  # Run cleanup every minute

    async def start_cleanup(self):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self.cleanup())

    async def stop_cleanup(self):
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        current_time = time.time()

        # Start cleanup task if not running
        await self.start_cleanup()

        if client_ip in self.requests:
            count, start_time = self.requests[client_ip]
            # Reset if minute has passed
            if current_time - start_time >= 60:
                self.requests[client_ip] = (1, current_time)
            else:
                # Check rate limit
                if count >= self.settings.RATE_LIMIT_PER_MINUTE:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please try again later."
                    )
                self.requests[client_ip] = (count + 1, start_time)
        else:
            self.requests[client_ip] = (1, current_time)

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    try:
        await rate_limiter.check_rate_limit(request)
        response = await call_next(request)
        return response
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        ) 