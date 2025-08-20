import logging

from pythonjsonlogger import jsonlogger

from src.config import settings
from src.utils.context_log import get_request_id


class RequestIDFilter(logging.Filter):
    """Logging filter that injects a per-request ID into each log record.

    The request ID is retrieved using a context-local variable, allowing
    asynchronous applications (like FastAPI) to maintain separate IDs
    across concurrent requests.

    If no request ID is set, 'unknown' will be used.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Injects the request ID into the log record.

        This method is automatically called by the logging framework.
        It adds a `request_id` attribute to the record using the context-local
        request ID, enabling logs to be correlated to a specific request.

        Args:
            record (logging.LogRecord): The log record being processed.

        Returns:
            bool: Always returns True to allow the record to be logged.
        """
        record.request_id = get_request_id() or "unknown"
        return True


def setup_log() -> None:
    """Configure structured logging for the application.

    - Sets up a StreamHandler using JSON formatting based on app settings.
    - Applies the RequestIDFilter to include a per-request ID in logs.
    - Sets the global log level from configuration.
    - Downgrades verbosity for common third-party libraries to WARNING.

    This should be called during application startup.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter(settings.jsonformat, json_ensure_ascii=False))
    handler.addFilter(RequestIDFilter())
    logging.basicConfig(level=settings.log_level, handlers=(handler,))

    for log_name in settings.excluded_logs:
        _logger = logging.getLogger(log_name)
        _logger.setLevel(logging.WARNING)
