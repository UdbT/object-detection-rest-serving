import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(name="fastapi_client", scope="module")
def fixture_fastapi_client() -> TestClient:
    """Fixture function to create a FastAPI test client.

    Returns:
        TestClient: A FastAPI test client instance.
    """
    return TestClient(app)
