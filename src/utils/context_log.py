import contextvars

# Create a ContextVar for request ID
request_id_ctx_var = contextvars.ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Retrieve the current request ID from the context variable.

    This function is typically used in asynchronous applications to
    get the request-specific identifier that was set earlier in the
    request lifecycle (e.g., by middleware). It ensures that each
    concurrent request can access its own isolated request ID.

    Returns:
        str or None: The current request ID if set, otherwise None.
    """
    return request_id_ctx_var.get()
