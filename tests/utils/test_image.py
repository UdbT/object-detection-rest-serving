import io
import numpy as np
import pytest
from pytest_mock import MockerFixture
from PIL import Image

from src.utils.image import get_file_size, apply_orientation_exif, get_file_type, ImageOps


def test_get_file_size_bytesio():
    raw = b"x" * (2 * 10**6)  # 2.0 MB by the function's definition
    bio = io.BytesIO(raw)
    assert pytest.approx(get_file_size(bio), rel=0, abs=1e-9) == 2.0


def test_apply_orientation_exif_no_orientation(mocker: MockerFixture, caplog):
    img = Image.new("RGB", (8, 8), color=(10, 20, 30))
    mocker.patch.object(img, "getexif", return_value={})  # no tag 274
    spy_transpose = mocker.spy(ImageOps, "exif_transpose")

    out = apply_orientation_exif(img)

    assert out is img
    assert spy_transpose.call_count == 0
    assert "image will be rotated/flipped" not in caplog.text


def test_apply_orientation_exif_with_orientation(mocker, caplog):
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


def _mk_image_bytes(fmt: str = "PNG", size=(5, 7), color=(4, 5, 6)) -> io.BytesIO:
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
def test_get_file_type_happy_path(fmt, expected_mime):
    img_bytes = _mk_image_bytes(fmt=fmt)
    mime, arr = get_file_type(img_bytes)

    assert mime == expected_mime
    assert isinstance(arr, np.ndarray)


def test_get_file_type_calls_apply_orientation_exif(mocker):
    img_bytes = _mk_image_bytes(fmt="PNG")

    patched = mocker.patch("src.utils.image.apply_orientation_exif", side_effect=lambda img: img)

    mime, arr = get_file_type(img_bytes)

    assert mime == "image/png"
    assert isinstance(arr, np.ndarray)
    patched.assert_called_once()
    assert isinstance(patched.call_args.args[0], Image.Image)
