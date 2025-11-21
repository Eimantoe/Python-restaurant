from contextvars import ContextVar
from uuid import uuid4
from typing import Optional

# Thread-safe context variable for async
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Functions to get, set, and generate correlation IDs
def get_correlation_id() -> Optional[str]:
    return correlation_id.get()

def set_correlation_id(corr_id: str) -> None:
    correlation_id.set(corr_id)

def generate_correlation_id() -> str:
    return str(uuid4())