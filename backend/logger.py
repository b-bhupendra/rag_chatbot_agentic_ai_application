import sys
from typing import Any

def log_info(message: Any) -> None:
    """Logs an informational message."""
    print(f"ℹ️  [INFO] {message}", flush=True)

def log_success(message: Any) -> None:
    """Logs a success message."""
    print(f"✅ [SUCCESS] {message}", flush=True)

def log_warning(message: Any) -> None:
    """Logs a warning message."""
    print(f"⚠️  [WARNING] {message}", file=sys.stderr, flush=True)

def log_error(message: Any) -> None:
    """Logs an error message."""
    print(f"❌ [ERROR] {message}", file=sys.stderr, flush=True)

