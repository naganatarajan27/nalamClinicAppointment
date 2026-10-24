"""Simple in-memory fixed-window rate limiter.

Suitable for a single-process deployment. For multi-instance production
deployments, replace with a shared store (e.g. Redis) behind the same
interface.
"""

import time
from collections import defaultdict
from threading import Lock


class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            attempts = [t for t in self._attempts[key] if now - t < self._window_seconds]
            self._attempts[key] = attempts
            return len(attempts) < self._max_attempts

    def record_attempt(self, key: str) -> None:
        with self._lock:
            self._attempts[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)


_login_limiter: InMemoryRateLimiter | None = None


def get_login_rate_limiter() -> InMemoryRateLimiter:
    global _login_limiter
    if _login_limiter is None:
        from app.core.config import get_settings

        settings = get_settings()
        _login_limiter = InMemoryRateLimiter(
            max_attempts=settings.login_rate_limit_attempts,
            window_seconds=settings.login_rate_limit_window_seconds,
        )
    return _login_limiter
