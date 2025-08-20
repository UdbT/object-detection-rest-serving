import inspect
import logging
import time
from functools import wraps

from src.config import settings

logger = logging.getLogger(__name__)


def timeit(func: callable) -> callable:
    """Decorator to time the execution of a function or coroutine.

    Args:
        func (callable): The function or coroutine to be timed.

    Returns:
        callable: A wrapper function that logs the execution time of the original function.
    """
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: list, **kwargs: dict) -> any:
            """Asynchronous wrapper to time the execution of a coroutine.

            Args:
                *args: Positional arguments for the wrapped function.
                **kwargs: Keyword arguments for the wrapped function.

            Returns:
            any: The result of the wrapped coroutine.
            """
            if not settings.enable_func_timing:
                return await func(*args, **kwargs)
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            end = time.perf_counter()
            logger.info(
                "Timing: %s executed in %.6f seconds",
                func.__name__,
                end - start,
                extra={"response_time": end - start, "function_name": func.__name__},
            )
            return result

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args: list, **kwargs: dict) -> any:
        """Synchronous wrapper to time the execution of a function.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            any: The result of the wrapped function.
        """
        if not settings.enable_func_timing:
            return func(*args, **kwargs)
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.info(
            "Timing: %s executed in %.6f seconds",
            func.__name__,
            end - start,
            extra={"response_time": end - start, "function_name": func.__name__},
        )
        return result

    return sync_wrapper
