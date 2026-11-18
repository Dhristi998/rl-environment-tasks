"""Token-bucket rate limiter."""


class TokenBucket:
    def __init__(self, capacity, refill_per_sec, now=0.0):
        if capacity <= 0 or refill_per_sec < 0:
            raise ValueError("invalid limiter settings")
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = capacity
        self.last = now

    def _refill(self, now):
        elapsed = now - self.last
        self.tokens = self.tokens + elapsed * self.refill_per_sec
        self.last = now

    def allow(self, now, cost=1):
        """Return True and spend `cost` tokens if enough are available."""
        self._refill(now)
        if self.tokens > cost:
            self.tokens -= cost
            return True
        return False
