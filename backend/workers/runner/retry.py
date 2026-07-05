from __future__ import annotations


class RetryPolicy:
    """Bounded exponential retry policy for worker jobs."""

    def __init__(self, *, max_attempts: int = 3, base_delay_seconds: int = 30, max_delay_seconds: int = 900) -> None:
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

    def next_delay_seconds(self, attempts: int) -> int:
        delay = self.base_delay_seconds * (2 ** max(attempts - 1, 0))
        return min(delay, self.max_delay_seconds)
