"""Retry logic with exponential backoff."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0

    # HTTP status codes that should not be retried
    no_retry_status_codes: set[int] = None

    def __post_init__(self):
        """Initialize default no-retry status codes."""
        if self.no_retry_status_codes is None:
            self.no_retry_status_codes = {400, 401, 403, 404, 422}


async def retry_with_backoff(
    func: Callable,
    *args,
    config: RetryConfig | None = None,
    **kwargs,
) -> Any:
    """
    Execute function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        config: Retry configuration (uses defaults if None)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries exhausted
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs)

            # Log recovery if this was a retry
            if attempt > 0:
                logger.info(
                    f"Retry succeeded on attempt {attempt + 1}/{config.max_attempts}"
                )

            return result

        except Exception as e:
            last_exception = e

            # Don't retry on client errors
            if hasattr(e, "status_code") and e.status_code in config.no_retry_status_codes:
                logger.warning(f"Client error {e.status_code}, not retrying")
                raise

            # Last attempt, don't wait
            if attempt == config.max_attempts - 1:
                logger.error(f"All {config.max_attempts} retry attempts exhausted")
                raise

            # Calculate backoff delay
            delay = min(
                config.base_delay * (config.exponential_base**attempt),
                config.max_delay,
            )

            logger.warning(
                f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )

            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
