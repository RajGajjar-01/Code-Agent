import logging
import sys
from typing import Any

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)

# Add handler to logger
if not audit_logger.handlers:
    audit_logger.addHandler(console_handler)


def log_analysis_start(file_path: str) -> None:
    """Log the start of file analysis."""
    audit_logger.info(f"Starting analysis of {file_path}")


def log_analysis_complete(file_path: str, findings: dict[str, Any]) -> None:
    """Log completion of file analysis with findings."""
    audit_logger.info(
        f"Completed analysis of {file_path}: "
        f"{findings.get('unused_imports', 0)} unused imports, "
        f"{findings.get('unused_functions', 0)} unused functions"
    )


def log_optimization_start(operation: str, target: str) -> None:
    """Log the start of an optimization operation."""
    audit_logger.info(f"Starting {operation} on {target}")


def log_optimization_complete(operation: str, target: str, success: bool) -> None:
    """Log completion of optimization operation."""
    status = "succeeded" if success else "failed"
    level = logging.INFO if success else logging.ERROR
    audit_logger.log(level, f"{operation} on {target} {status}")


def log_error(operation: str, error: Exception) -> None:
    """Log an error during audit operations."""
    audit_logger.error(f"Error during {operation}: {str(error)}", exc_info=True)


def log_warning(message: str) -> None:
    """Log a warning message."""
    audit_logger.warning(message)
