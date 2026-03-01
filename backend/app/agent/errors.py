"""Error handling and response structures."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ErrorResponse:
    """Structured error response for tool execution failures."""

    error_type: str  # "client_error", "server_error", "network_error", "circuit_open"
    message: str
    details: Optional[dict] = None
    retry_count: int = 0
    suggestions: Optional[list[str]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "retry_count": self.retry_count,
            "suggestions": self.suggestions,
        }


def categorize_error(exception: Exception) -> str:
    """
    Categorize an exception into error types.

    Args:
        exception: The exception to categorize

    Returns:
        Error type string
    """
    # Check for HTTP status codes
    if hasattr(exception, "status_code"):
        status_code = exception.status_code
        if 400 <= status_code < 500:
            return "client_error"
        elif 500 <= status_code < 600:
            return "server_error"

    # Check for network-related errors
    error_str = str(exception).lower()
    if any(
        keyword in error_str
        for keyword in ["connection", "timeout", "network", "dns", "unreachable"]
    ):
        return "network_error"

    # Check for circuit breaker errors
    if "circuit" in error_str or "CircuitBreakerOpenError" in str(type(exception)):
        return "circuit_open"

    # Default to generic error
    return "unknown_error"


def create_error_response(
    exception: Exception, retry_count: int = 0, context: Optional[str] = None
) -> ErrorResponse:
    """
    Create a structured error response from an exception.

    Args:
        exception: The exception that occurred
        retry_count: Number of retry attempts made
        context: Additional context about what was being attempted

    Returns:
        Structured ErrorResponse
    """
    error_type = categorize_error(exception)
    message = str(exception)

    # Add context if provided
    if context:
        message = f"{context}: {message}"

    # Generate suggestions based on error type
    suggestions = []
    if error_type == "client_error":
        suggestions.append("Check the input parameters and try again")
        suggestions.append("Verify the resource exists and you have permission")
    elif error_type == "server_error":
        suggestions.append("The service may be temporarily unavailable")
        suggestions.append("Try again in a few moments")
    elif error_type == "network_error":
        suggestions.append("Check your network connection")
        suggestions.append("Verify the service URL is correct")
    elif error_type == "circuit_open":
        suggestions.append("The service is currently unavailable")
        suggestions.append("Wait for the circuit breaker to recover")
        suggestions.append("Try a different approach or tool")

    details = {}
    if hasattr(exception, "status_code"):
        details["status_code"] = exception.status_code
    if hasattr(exception, "__class__"):
        details["exception_type"] = exception.__class__.__name__

    return ErrorResponse(
        error_type=error_type,
        message=message,
        details=details if details else None,
        retry_count=retry_count,
        suggestions=suggestions if suggestions else None,
    )
