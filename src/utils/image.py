import logging
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def get_file_size(file_byte: BytesIO) -> float:
    """Get file size from file on BytesIO format.

    Args:
        file_byte: BytesIO

    Returns:
        float: file size in mega bytes (MB)
    """
    return file_byte.getbuffer().nbytes / (10**6)


def apply_orientation_exif(image: Image) -> Image:
    """Convert image according to exif data (currently support only orientation).

    Args:
        image (Image): PIL image

    Returns:
        Image: applied image
    """
    # Get exif data
    img_exif = image.getexif()

    # Get orientation from exif tag 274
    if orientation := img_exif.get(274):
        logger.warning("image will be rotated/flipped with orientation %d", orientation)
        image = ImageOps.exif_transpose(image)

    return image


def get_file_type(img_byte: BytesIO) -> tuple[str, np.ndarray]:
    """Verify image type.

    Args:
        img_byte: BytesIO

    Returns:
        str: image's type
        np.ndarray: image in ndarray
    """
    img = Image.open(img_byte)
    converted_img = img.convert("RGB")
    converted_img = apply_orientation_exif(converted_img)
    return img.get_format_mimetype(), np.array(converted_img)
