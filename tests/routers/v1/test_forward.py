
import pytest
from fastapi.testclient import TestClient


class TestForwardEndpoint:
    """Test class for the /v1/forward endpoint.

    This class contains all unit tests for the object detection forward endpoint,
    including success cases, error handling, and data validation scenarios.
    """

    def test_forward_valid_image_success(
        self, fastapi_client: TestClient, valid_image_base64: str
    ) -> None:
        """Test successful object detection with a valid image.

        This test verifies that the endpoint correctly processes a valid image
        and returns proper detection results with the expected response structure.

        Args:
            fastapi_client: FastAPI test client instance.
            valid_image_base64: Base64 encoded valid test image string.

        Returns:
            None

        Raises:
            AssertionError: If the response structure or data is invalid.
        """
        payload = {"image": valid_image_base64}
        expected_status_code = 200

        response = fastapi_client.post("/v1/forward", json=payload)

        # Assert
        assert response.status_code == expected_status_code
        response_data = response.json()

        # Check response structure
        assert "detections" in response_data
        assert isinstance(response_data["detections"], list)

        # If detections are found, validate their structure
        if response_data["detections"]:
            detection = response_data["detections"][0]
            assert "bbox" in detection
            assert "score" in detection
            assert "label" in detection
            assert isinstance(detection["bbox"], list)
            assert len(detection["bbox"]) == 4  # [x1, y1, x2, y2]
            assert isinstance(detection["score"], (int, float))
            assert isinstance(detection["label"], str)

    def test_forward_blank_image_success(
        self, fastapi_client: TestClient, blank_image_base64: str
    ) -> None:
        """Test object detection with a blank image.

        This test verifies that the endpoint handles blank images correctly
        and returns a valid response structure, even if no objects are detected.

        Args:
            fastapi_client: FastAPI test client instance.
            blank_image_base64: Base64 encoded blank test image string.

        Returns:
            None

        Raises:
            AssertionError: If the response structure is invalid.
        """
        payload = {"image": blank_image_base64}
        expected_status_code = 200

        response = fastapi_client.post("/v1/forward", json=payload)

        # Assert
        assert response.status_code == expected_status_code
        response_data = response.json()

        # Check response structure
        assert "detections" in response_data
        assert isinstance(response_data["detections"], list)

    @pytest.mark.parametrize(
        "test_case,payload,expected_status_code",
        [
            (
                "large_image",
                {"image": "large_image_base64"},
                422,
            ),
            (
                "invalid_image_type",
                {"image": "invalid_image_base64"},
                422,
            ),
            (
                "invalid_base64",
                {"image": "invalid_base64_string"},
                422,
            ),
            (
                "missing_image_field",
                {},
                422,
            ),
            (
                "empty_image_field",
                {"image": ""},
                422,
            ),
        ],
    )
    def test_forward_validation_errors(
        self,
        fastapi_client: TestClient,
        test_case: str,
        payload: dict,
        expected_status_code: int,
        large_image_base64: str,
        invalid_image_base64: str,
        invalid_base64_string: str,
    ) -> None:
        """Test object detection with various validation errors.

        This parameterized test covers multiple error scenarios including
        large images, invalid file types, malformed base64 strings,
        missing fields, and empty fields.

        Args:
            fastapi_client: FastAPI test client instance.
            test_case: Test case identifier string.
            payload: Request payload dictionary.
            expected_status_code: Expected HTTP status code integer.
            large_image_base64: Base64 encoded large test image string.
            invalid_image_base64: Base64 encoded invalid image type string.
            invalid_base64_string: Invalid base64 string for testing.

        Returns:
            None

        Raises:
            AssertionError: If the response status or structure is invalid.
        """
        # Replace placeholder values with actual fixture values
        if test_case == "large_image":
            payload["image"] = large_image_base64
        elif test_case == "invalid_image_type":
            payload["image"] = invalid_image_base64
        elif test_case == "invalid_base64":
            payload["image"] = invalid_base64_string

        response = fastapi_client.post("/v1/forward", json=payload)

        # Assert
        assert response.status_code == expected_status_code
        response_data = response.json()
        assert "detail" in response_data

    def test_forward_wrong_http_method_error(self, fastapi_client: TestClient) -> None:
        """Test object detection with wrong HTTP method.

        This test verifies that the endpoint correctly rejects requests
        that use the wrong HTTP method (GET instead of POST).

        Args:
            fastapi_client: FastAPI test client instance.

        Returns:
            None

        Raises:
            AssertionError: If the response status code is not 405.
        """
        expected_status_code = 405  # Method Not Allowed

        response = fastapi_client.get("/v1/forward")

        # Assert
        assert response.status_code == expected_status_code

    def test_forward_detection_scores_range(
        self, fastapi_client: TestClient, valid_image_base64: str
    ) -> None:
        """Test that detection scores are within valid range [0, 1].

        This test verifies that all detection confidence scores returned
        by the API are within the expected range of 0.0 to 1.0.

        Args:
            fastapi_client: FastAPI test client instance.
            valid_image_base64: Base64 encoded valid test image string.

        Returns:
            None

        Raises:
            AssertionError: If any detection score is outside the valid range.
        """
        payload = {"image": valid_image_base64}

        response = fastapi_client.post("/v1/forward", json=payload)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        for detection in response_data["detections"]:
            score = detection["score"]
            assert 0.0 <= score <= 1.0, f"Score {score} is not in range [0, 1]"

    def test_forward_bbox_coordinates_validity(
        self, fastapi_client: TestClient, valid_image_base64: str
    ) -> None:
        """Test that bounding box coordinates are valid (x2 > x1, y2 > y1).

        This test verifies that all bounding box coordinates follow the
        expected format where x2 > x1 and y2 > y1.

        Args:
            fastapi_client: FastAPI test client instance.
            valid_image_base64: Base64 encoded valid test image string.

        Returns:
            None

        Raises:
            AssertionError: If any bounding box coordinates are invalid.
        """
        payload = {"image": valid_image_base64}

        response = fastapi_client.post("/v1/forward", json=payload)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        for detection in response_data["detections"]:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = bbox
            assert x2 > x1, f"Invalid bbox: x2 ({x2}) should be greater than x1 ({x1})"
            assert y2 > y1, f"Invalid bbox: y2 ({y2}) should be greater than y1 ({y1})"

    def test_forward_multiple_detections_structure(
        self, fastapi_client: TestClient, valid_image_base64: str
    ) -> None:
        """Test that multiple detections have consistent structure.

        This test verifies that when multiple objects are detected,
        all detection objects have the same structure and keys.

        Args:
            fastapi_client: FastAPI test client instance.
            valid_image_base64: Base64 encoded valid test image string.

        Returns:
            None

        Raises:
            AssertionError: If detection structures are inconsistent.
        """
        payload = {"image": valid_image_base64}

        response = fastapi_client.post("/v1/forward", json=payload)

        # Assert
        assert response.status_code == 200
        response_data = response.json()

        if len(response_data["detections"]) > 1:
            # Check that all detections have the same structure
            first_detection_keys = set(response_data["detections"][0].keys())
            for detection in response_data["detections"][1:]:
                assert (
                    set(detection.keys()) == first_detection_keys
                ), "All detections should have the same structure"
