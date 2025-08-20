import io

import numpy as np
import pytest
from PIL import Image
from pytest_mock import MockerFixture

from src.utils.image import (
    ImageOps,
    apply_orientation_exif,
    get_file_size,
    get_file_type,
)


def test_get_file_size_bytesio() -> None:
    """Test file size calculation from BytesIO object.

    Returns:
        None

    Raises:
        AssertionError: If the calculated file size is not approximately 2.0 MB.
    """
    raw = b"x" * (2 * 10**6)  # 2.0 MB by the function's definition
    bio = io.BytesIO(raw)
    assert pytest.approx(get_file_size(bio), rel=0, abs=1e-9) == 2.0


def test_apply_orientation_exif_no_orientation(mocker: MockerFixture, caplog) -> None:
    """Test EXIF orientation handling when no orientation tag is present.

    Args:
        mocker: Pytest mocker fixture for creating mocks.
        caplog: Pytest caplog fixture for capturing log messages.

    Returns:
        None

    Raises:
        AssertionError: If the image is modified or warnings are logged unexpectedly.
    """
    img = Image.new("RGB", (8, 8), color=(10, 20, 30))
    mocker.patch.object(img, "getexif", return_value={})  # no tag 274
    spy_transpose = mocker.spy(ImageOps, "exif_transpose")

    out = apply_orientation_exif(img)

    assert out is img
    assert spy_transpose.call_count == 0
    assert "image will be rotated/flipped" not in caplog.text


def test_apply_orientation_exif_with_orientation(mocker: MockerFixture, caplog) -> None:
    """Test EXIF orientation handling when orientation tag is present.

    Args:
        mocker: Pytest mocker fixture for creating mocks.
        caplog: Pytest caplog fixture for capturing log messages.

    Returns:
        None

    Raises:
        AssertionError: If the orientation is not applied correctly or warnings are not logged.
    """
    img = Image.new("RGB", (8, 8), color=(1, 2, 3))
    mocker.patch.object(img, "getexif", return_value={274: 6})  # orientation present

    rotated = Image.new("RGB", (8, 8), color=(9, 9, 9))
    exif_transpose = mocker.patch(
        "src.utils.image.ImageOps.exif_transpose",
        autospec=True,
        return_value=rotated,
    )

    with caplog.at_level("WARNING"):
        out = apply_orientation_exif(img)

    assert out is rotated
    exif_transpose.assert_called_once_with(img)
    assert "orientation 6" in caplog.text


def _mk_image_bytes(
    fmt: str = "PNG", size: tuple = (5, 7), color: tuple = (4, 5, 6)
) -> io.BytesIO:
    """Create a test image as BytesIO object.

    Args:
        fmt: Image format string (PNG, JPEG, BMP, etc.).
        size: Image dimensions as (width, height) tuple.
        color: RGB color values as (r, g, b) tuple.

    Returns:
        BytesIO: A BytesIO object containing the test image data.
    """
    im = Image.new("RGB", size=size, color=color)
    bio = io.BytesIO()
    im.save(bio, format=fmt)
    bio.seek(0)
    return bio


@pytest.mark.parametrize(
    "fmt, expected_mime",
    [
        ("PNG", "image/png"),
        ("JPEG", "image/jpeg"),
        ("BMP", "image/bmp"),
    ],
)
def test_get_file_type_happy_path(fmt: str, expected_mime: str) -> None:
    """Test file type detection for various image formats.

    Args:
        fmt: Image format string to test.
        expected_mime: Expected MIME type string.

    Returns:
        None

    Raises:
        AssertionError: If the MIME type or array type is incorrect.
    """
    img_bytes = _mk_image_bytes(fmt=fmt)
    mime, arr = get_file_type(img_bytes)

    assert mime == expected_mime
    assert isinstance(arr, np.ndarray)


def test_get_file_type_calls_apply_orientation_exif(mocker: MockerFixture) -> None:
    """Test that get_file_type calls the orientation correction function.

    Args:
        mocker: Pytest mocker fixture for creating mocks.

    Returns:
        None

    Raises:
        AssertionError: If the orientation function is not called or called incorrectly.
    """
    img_bytes = _mk_image_bytes(fmt="PNG")

    patched = mocker.patch(
        "src.utils.image.apply_orientation_exif", side_effect=lambda img: img
    )

    mime, arr = get_file_type(img_bytes)

    assert mime == "image/png"
    assert isinstance(arr, np.ndarray)
    patched.assert_called_once()
    assert isinstance(patched.call_args.args[0], Image.Image)
