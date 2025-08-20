from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(fastapi_client: TestClient) -> None:
    """Test function to verify the behavior of the 'health_check' API endpoint.

    Args:
        mocker (MockerFixture): The pytest mocker fixture.
        fastapi_client (TestClient): FastAPI test client instance.

    """
    result = fastapi_client.get("/health_check")
    assert result.status_code == status.HTTP_200_OK
