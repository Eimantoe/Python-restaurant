import logging
import sys
import structlog
from Shared.config import settings

def configure_logging(is_dev_mode=True):
    """
    Configures logging for the application.
    In development mode, logs are human-readable and colored.
    In production mode, logs are JSON-formatted.
    """
    # 1. Define the processor chain
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if is_dev_mode:
        # Development-friendly logging
        processors = shared_processors + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True), # Pretty, colored output
        ]
    else:
        # Production-ready JSON logging
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(), # Render to JSON
        ]

    # 2. Configure structlog to wrap the standard logging library
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 3. Configure the standard logging library to pass messages to structlog
    # This ensures logs from other libraries (e.g., SQLAlchemy) are also structured.
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")

configure_logging(is_dev_mode=settings.debug_mode)

logger = structlog.get_logger("Kitchen microservices")