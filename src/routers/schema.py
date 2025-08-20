import base64
from io import BytesIO

import numpy as np
from PIL import UnidentifiedImageError
from pydantic import BaseModel, Field, field_validator

from src.config import settings
from src.utils.image import get_file_size, get_file_type


class ObjectDetectionRequest(BaseModel):
    """Request model for object detection API."""

    image: str = Field(..., description="Base64 encoded image string")

    @field_validator("image")
    def check_image(cls, content: str) -> np.ndarray: # noqa: N805
        """Validate and process the input image.

        Args:
            content (str): Base64 encoded image string.

        Returns:
            np.ndarray: Processed image array.

        Raises:
            ValueError: If the image is invalid or cannot be processed.
        """
        try:
            img_byte = BytesIO(base64.b64decode(content))
            if get_file_size(img_byte) > settings.max_size_mb_threshold:
                raise ValueError("INPUT_SIZE_TOO_LARGE") # noqa: EM101
            img_type, img_arr = get_file_type(img_byte)
        except base64.binascii.Error as err:
            raise ValueError("INVALID_BASE64") from err # noqa: EM101
        except (UnidentifiedImageError, OSError) as err:
            raise ValueError("UNREADABLE_IMAGE") from err # noqa: EM101

        if img_type not in [f"image/{_type}" for _type in settings.allow_image_types]:
            raise ValueError("INVALID_FILE_TYPE") # noqa: EM101

        return img_arr


class DetectedObject(BaseModel):
    """Model representing a detected object."""

    bbox: list[float] = Field(..., description="Bounding box coordinates [x, y, x2, y2]")
    score: float = Field(..., description="Detection score")
    label: str = Field(..., description="Class label of the detected object")


class ObjectDetectionResponse(BaseModel):
    """Response model for object detection API."""

    detections: list[DetectedObject] = Field(..., description="List of detected objects")
