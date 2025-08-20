import uuid

from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.utils.context_log import request_id_ctx_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts or generates a request ID for each incoming request.

    - For POST, PUT, or PATCH requests, it attempts to read `X-Request-ID` from the header.
    - If `X-Request-ID` is not provided, a new UUID is generated.
    - The request ID is stored in a context-local variable, allowing it to be accessed
      throughout the request lifecycle (e.g., in log filters).
    - Adds the request ID to the response headers as `X-Request-ID`.
    """

    async def dispatch(self, request: Request, call_next: callable) -> Response:
        """Process the incoming request to assign a unique request ID.

        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or route handler in the chain.

        Returns:
            Response: The HTTP response, with the `X-Request-ID` header included.
        """
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
