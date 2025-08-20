from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
from pytest_mock import MockerFixture

import src.models.object_detector as od


class FakeIO:
    """Mock class for ONNX input/output metadata."""

    def __init__(self, name: str, shape: list) -> None:
        """Initialize a fake ONNX input/output object.

        Args:
            name: The name of the input/output tensor.
            shape: The shape of the input/output tensor.
        """
        self.name = name
        self.shape = shape


@pytest.fixture
def fake_session(mocker: MockerFixture) -> MagicMock:
    """Create a mocked ONNX runtime session with predetermined I/O names and shapes.

    Args:
        mocker: Pytest mocker fixture for creating mocks.

    Returns:
        MagicMock: A mocked ONNX InferenceSession instance.
    """
    sess = mocker.MagicMock()
    sess.get_inputs.return_value = [FakeIO("in_0", [1, 3, 4, 5])]
    sess.get_outputs.return_value = [FakeIO("out_0", None)]
    return sess


@pytest.fixture
def patched_session_ctor(mocker: MockerFixture, fake_session: MagicMock) -> MagicMock:
    """Patch the ONNX InferenceSession constructor to return our fake session.

    Args:
        mocker: Pytest mocker fixture for creating mocks.
        fake_session: The mocked ONNX session to return.

    Returns:
        MagicMock: The patched InferenceSession constructor.
    """
    return mocker.patch.object(od.ort, "InferenceSession", return_value=fake_session)


@pytest.fixture
def detector(patched_session_ctor: MagicMock) -> od.ObjectDetector:
    """Create an ObjectDetector instance with mocked dependencies.

    This fixture creates an ObjectDetector instance using the patched
    ONNX session constructor for isolated testing.

    Args:
        patched_session_ctor: The patched ONNX session constructor.

    Returns:
        ObjectDetector: An ObjectDetector instance with mocked dependencies.
    """
    return od.ObjectDetector("model.onnx")


@pytest.fixture
def fake_settings(monkeypatch) -> SimpleNamespace:
    """Create fake settings for testing configuration-dependent behavior.

    This fixture creates a mock settings object with test values
    and patches the module's settings reference.

    Args:
        monkeypatch: Pytest monkeypatch fixture for modifying module attributes.

    Returns:
        SimpleNamespace: A mock settings object with test configuration values.
    """
    ns = SimpleNamespace(
        conf_thres=0.5,
        iou_thres=0.45,
        coco_classes=["class0", "class1"],
    )
    # Replace the settings object used inside the module under test
    monkeypatch.setattr(od, "settings", ns, raising=False)
    return ns


def test_init_sets_io_and_shape(
    patched_session_ctor: MagicMock, fake_session: MagicMock
) -> None:
    """Test that ObjectDetector initialization correctly sets I/O metadata and dimensions.

    Args:
        patched_session_ctor: The patched ONNX session constructor.
        fake_session: The mocked ONNX session instance.

    Returns:
        None

    Raises:
        AssertionError: If the I/O metadata or dimensions are not set correctly.
    """
    det = od.ObjectDetector("m.onnx")
    patched_session_ctor.assert_called_once_with(
        "m.onnx", providers=["CPUExecutionProvider"]
    )
    assert det.session is fake_session
    assert det.input_name == "in_0"
    assert det.output_name == "out_0"
    assert det.input_shape == [1, 3, 4, 5]
    assert (det.height, det.width) == (4, 5)


def test_preprocess_pipeline(
    detector: od.ObjectDetector, mocker: MockerFixture
) -> None:
    """Test the complete image preprocessing pipeline.

    Args:
        detector: ObjectDetector instance with mocked dependencies.
        mocker: Pytest mocker fixture for creating mocks.

    Returns:
        None

    Raises:
        AssertionError: If the preprocessing pipeline doesn't work correctly.
    """
    resized = np.full((4, 5, 3), [1, 2, 3], dtype=np.uint8)  # B,G,R constant
    resize = mocker.patch.object(od.cv2, "resize", return_value=resized)

    cvt = mocker.patch.object(
        od.cv2, "cvtColor", side_effect=lambda img, code: img[..., ::-1]
    )

    # BGR to RGB conversion
    x = np.zeros((7, 9, 3), dtype=np.uint8)
    out = detector._preprocess(x)

    resize.assert_called_once_with(x, (detector.width, detector.height))  # (W,H)
    cvt.assert_called_once()

    # shape and type
    assert out.shape == (1, 3, 4, 5)
    assert out.dtype == np.float32


def test_infer_calls_session_run(detector: od.ObjectDetector) -> None:
    """Test that inference correctly calls the ONNX session run method.

    Args:
        detector: ObjectDetector instance with mocked dependencies.

    Returns:
        None

    Raises:
        AssertionError: If the session run method is not called correctly.
    """
    detector.session.run.return_value = [np.array([[42]], dtype=np.float32)]
    fake_in = np.zeros((1, 3, 4, 5), dtype=np.float32)

    out = detector._infer(fake_in)

    detector.session.run.assert_called_once_with(
        [detector.output_name], {detector.input_name: fake_in}
    )
    assert isinstance(out, np.ndarray)
    assert out[0, 0] == 42


def test_postprocess_happy_path(
    detector: od.ObjectDetector, mocker: MockerFixture, fake_settings: SimpleNamespace
) -> None:
    """Test the postprocessing pipeline with successful detections.

    Args:
        detector: ObjectDetector instance with mocked dependencies.
        mocker: Pytest mocker fixture for creating mocks.
        fake_settings: Mock settings object with test configuration.

    Returns:
        None

    Raises:
        AssertionError: If the postprocessing pipeline doesn't work correctly.
    """
    boxes_xywh = np.array([[10, 10, 4, 6], [20, 20, 10, 10]], dtype=np.float32)
    logits = np.array([[0.1, 0.9], [0.8, 0.2]], dtype=np.float32)
    xyxy = np.array([[8, 7, 12, 13], [15, 15, 25, 25]], dtype=np.float32)

    mocker.patch.object(od, "split_fields", return_value=(boxes_xywh, logits))
    mocker.patch.object(od, "logits_to_probs", return_value=logits)
    mocker.patch.object(od, "xywh_to_xyxy", return_value=xyxy)
    mocker.patch.object(od, "rescale_xyxy", return_value=xyxy)
    mocker.patch.object(
        od,
        "filter_by_conf",
        return_value=(xyxy, logits.max(axis=1), logits.argmax(axis=1)),
    )
    mocker.patch.object(od.cv2.dnn, "NMSBoxes", return_value=[[0]])  # keep index 0

    preds = np.zeros((1, 6, 2), dtype=np.float32)
    dets = detector._postprocess(preds, image_shape=(480, 640))

    assert isinstance(dets, list) and len(dets) == 1
    bbox, score, label = dets[0]
    assert np.allclose(bbox, xyxy[0])
    assert np.isclose(score, 0.9)
    assert label == "class1"


def test_postprocess_no_detections(
    detector: od.ObjectDetector, mocker: MockerFixture
) -> None:
    """Test the postprocessing pipeline when no objects are detected.

    Args:
        detector: ObjectDetector instance with mocked dependencies.
        mocker: Pytest mocker fixture for creating mocks.

    Returns:
        None

    Raises:
        AssertionError: If the postprocessing doesn't handle empty detections correctly.
    """
    mocker.patch.object(
        od, "split_fields", return_value=(np.zeros((0, 4)), np.zeros((0, 2)))
    )
    mocker.patch.object(od, "logits_to_probs", return_value=np.zeros((0, 2)))
    mocker.patch.object(od, "xywh_to_xyxy", return_value=np.zeros((0, 4)))
    mocker.patch.object(od, "rescale_xyxy", return_value=np.zeros((0, 4)))
    mocker.patch.object(
        od,
        "filter_by_conf",
        return_value=(np.zeros((0, 4)), np.zeros((0,)), np.zeros((0,), dtype=int)),
    )

    mocker.patch.object(od.cv2.dnn, "NMSBoxes", return_value=[])

    dets = detector._postprocess(np.zeros((1, 6, 0)), image_shape=(100, 200))
    assert dets == []


def test_forward_wires_methods(
    detector: od.ObjectDetector, mocker: MockerFixture, fake_settings: SimpleNamespace
) -> None:
    """Test that the forward method correctly wires all internal methods together.

    Args:
        detector: ObjectDetector instance with mocked dependencies.
        mocker: Pytest mocker fixture for creating mocks.
        fake_settings: Mock settings object with test configuration.

    Returns:
        None

    Raises:
        AssertionError: If the forward method doesn't wire the methods correctly.
    """
    pre = mocker.patch.object(detector, "_preprocess", return_value="P")
    infer = mocker.patch.object(detector, "_infer", return_value="O")
    post = mocker.patch.object(
        detector, "_postprocess", return_value=[(np.array([1, 2, 3, 4]), 0.9, "dog")]
    )

    inp = np.zeros((100, 200, 3), dtype=np.uint8)
    out = detector.forward(inp)

    pre.assert_called_once_with(inp)
    infer.assert_called_once_with("P")
    post.assert_called_once_with("O", (100, 200))

    assert "detections" in out and len(out["detections"]) == 1
    bbox, score, label = out["detections"][0]
    np.testing.assert_allclose(bbox, np.array([1, 2, 3, 4]))
    assert score == pytest.approx(0.9)
    assert label == "dog"
