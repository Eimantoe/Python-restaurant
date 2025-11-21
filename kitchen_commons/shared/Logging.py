import logging
import sys
import structlog
from kitchen_commons.shared.Settings import settings
from .Correlation import get_correlation_id

def configure_logging(is_dev_mode=True):

    # Custom processor to add correlation ID to log entries
    def add_correlation_id(logger, method_name, event_dict):
        corr_id = get_correlation_id()
        if corr_id:
            event_dict['correlation_id'] = corr_id
        return event_dict

    # 1. Define the processor chain
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_correlation_id,
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