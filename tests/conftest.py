"""Test configuration and fixtures for the object detection API tests.

This module provides shared fixtures and configuration for all test modules,
including FastAPI test client setup and test image fixtures.
"""

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.main import app
from src.models.object_detector import ObjectDetector


@pytest.fixture(name="fastapi_client", scope="module")
def fixture_fastapi_client() -> TestClient:
    """Create a FastAPI test client with initialized object detector.

    This fixture creates a test client and manually initializes the object
    detector in the app state to ensure the model is available for testing.

    Returns:
        TestClient: A configured FastAPI test client instance.

    Note:
        The object detector is manually initialized because TestClient doesn't
        automatically trigger the lifespan function.
    """
    # Manually initialize the object detector in app state
    app.state.object_detector = ObjectDetector(settings.model_path)

    return TestClient(app)


@pytest.fixture(name="test_assets_dir", scope="module")
def fixture_test_assets_dir() -> Path:
    """Get the path to the test assets directory.

    This fixture provides the absolute path to the directory containing
    test images and other test assets.

    Returns:
        Path: Absolute path to the test assets directory.
    """
    return Path(__file__).parent / "assets"


@pytest.fixture(name="valid_image_base64", scope="module")
def fixture_valid_image_base64(test_assets_dir: Path) -> str:
    """Provide a valid test image as base64 string.

    This fixture loads a valid JPEG image from the test assets directory
    and returns it as a base64 encoded string for testing successful
    object detection scenarios.

    Args:
        test_assets_dir: Path to the test assets directory.

    Returns:
        str: Base64 encoded image string for valid image testing.

    Raises:
        FileNotFoundError: If the image file doesn't exist.
    """
    image_path = test_assets_dir / "image.jpg"
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")


@pytest.fixture(name="large_image_base64", scope="module")
def fixture_large_image_base64(test_assets_dir: Path) -> str:
    """Provide a large test image as base64 string.

    This fixture loads a large image file from the test assets directory
    and returns it as a base64 encoded string for testing file size
    validation scenarios.

    Args:
        test_assets_dir: Path to the test assets directory.

    Returns:
        str: Base64 encoded image string for large image testing.

    Raises:
        FileNotFoundError: If the image file doesn't exist.
    """
    image_path = test_assets_dir / "large.jpg"
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")


@pytest.fixture(name="blank_image_base64", scope="module")
def fixture_blank_image_base64(test_assets_dir: Path) -> str:
    """Provide a blank test image as base64 string.

    This fixture loads a blank PNG image from the test assets directory
    and returns it as a base64 encoded string for testing edge cases
    where no objects should be detected.

    Args:
        test_assets_dir: Path to the test assets directory.

    Returns:
        str: Base64 encoded image string for blank image testing.

    Raises:
        FileNotFoundError: If the image file doesn't exist.
    """
    image_path = test_assets_dir / "blank.png"
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")


@pytest.fixture(name="invalid_image_base64", scope="module")
def fixture_invalid_image_base64(test_assets_dir: Path) -> str:
    """Provide an invalid test image as base64 string.

    This fixture loads an unsupported image format (WebP) from the test
    assets directory and returns it as a base64 encoded string for
    testing file type validation scenarios.

    Args:
        test_assets_dir: Path to the test assets directory.

    Returns:
        str: Base64 encoded image string for invalid image type testing.

    Raises:
        FileNotFoundError: If the image file doesn't exist.
    """
    image_path = test_assets_dir / "wrong_type.webp"
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    return base64.b64encode(image_bytes).decode("utf-8")


@pytest.fixture(name="invalid_base64_string", scope="module")
def fixture_invalid_base64_string() -> str:
    """Provide an invalid base64 string for testing.

    This fixture returns a string that is not valid base64 encoded
    data for testing base64 validation scenarios.

    Returns:
        str: Invalid base64 string for testing validation errors.
    """
    return "invalid_base64_string"
