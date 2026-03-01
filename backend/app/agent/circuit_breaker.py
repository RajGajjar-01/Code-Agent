import logging
import time
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time > self.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker '{self.name}': transitioning to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable, failing fast."
                )

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception:
            self.on_failure()
            raise

    def on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info(
                f"Circuit breaker '{self.name}': closing after successful test"
            )

        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}': OPEN after {self.failure_count} failures"
            )

    def reset(self):
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED