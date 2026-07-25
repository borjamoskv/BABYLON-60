import time
import asyncio
from typing import Optional

class RateLimiter:
    def __init__(self, rate_limit_rpm: int = 100) -> None:
        self.rate_limit_rpm = rate_limit_rpm
        self.tokens = float(rate_limit_rpm)
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            
            # refill
            self.tokens += elapsed * (self.rate_limit_rpm / 60.0)
            if self.tokens > self.rate_limit_rpm:
                self.tokens = float(self.rate_limit_rpm)
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False
