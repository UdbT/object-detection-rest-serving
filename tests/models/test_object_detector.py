from types import SimpleNamespace
from unittest.mock import MagicMock
import numpy as np
import pytest
from pytest_mock import MockerFixture

import src.models.object_detector as od


class FakeIO:
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape


@pytest.fixture
def fake_session(mocker: MockerFixture) -> MagicMock:
    """Mocked onnxruntime session with predetermined I/O names & shapes."""
    sess = mocker.MagicMock()
    sess.get_inputs.return_value = [FakeIO("in_0", [1, 3, 4, 5])]
    sess.get_outputs.return_value = [FakeIO("out_0", None)]
    return sess


@pytest.fixture
def patched_session_ctor(mocker: MockerFixture, fake_session: MagicMock) -> MagicMock:
    """Patch ort.InferenceSession to return our fake session."""
    return mocker.patch.object(od.ort, "InferenceSession", return_value=fake_session)


@pytest.fixture
def detector(patched_session_ctor: MagicMock) -> od.ObjectDetector:
    """Construct the detector with the mocked session."""
    return od.ObjectDetector("model.onnx")


@pytest.fixture
def fake_settings(monkeypatch):
    ns = SimpleNamespace(
        conf_thres=0.5,
        iou_thres=0.45,
        coco_classes=["class0", "class1"],
    )
    # Replace the settings object used inside the module under test
    monkeypatch.setattr(od, "settings", ns, raising=False)
    return ns


def test_init_sets_io_and_shape(patched_session_ctor: MagicMock, fake_session: MagicMock) -> None:
    det = od.ObjectDetector("m.onnx")
    patched_session_ctor.assert_called_once_with("m.onnx", providers=["CPUExecutionProvider"])
    assert det.session is fake_session
    assert det.input_name == "in_0"
    assert det.output_name == "out_0"
    assert det.input_shape == [1, 3, 4, 5]
    assert (det.height, det.width) == (4, 5)


def test_preprocess_pipeline(detector: od.ObjectDetector, mocker: MockerFixture) -> None:
    resized = np.full((4, 5, 3), [1, 2, 3], dtype=np.uint8)  # B,G,R constant
    resize = mocker.patch.object(od.cv2, "resize", return_value=resized)

    cvt = mocker.patch.object(od.cv2, "cvtColor", side_effect=lambda img, code: img[..., ::-1])

    # BGR to RGB conversion
    x = np.zeros((7, 9, 3), dtype=np.uint8)
    out = detector._preprocess(x)

    resize.assert_called_once_with(x, (detector.width, detector.height))  # (W,H)
    cvt.assert_called_once()

    # shape and type
    assert out.shape == (1, 3, 4, 5)
    assert out.dtype == np.float32


def test_infer_calls_session_run(detector: od.ObjectDetector) -> None:
    detector.session.run.return_value = [np.array([[42]], dtype=np.float32)]
    fake_in = np.zeros((1, 3, 4, 5), dtype=np.float32)

    out = detector._infer(fake_in)

    detector.session.run.assert_called_once_with([detector.output_name], {detector.input_name: fake_in})
    assert isinstance(out, np.ndarray)
    assert out[0, 0] == 42


def test_postprocess_happy_path(
    detector: od.ObjectDetector, mocker: MockerFixture, fake_settings: SimpleNamespace
) -> None:
    boxes_xywh = np.array([[10, 10, 4, 6], [20, 20, 10, 10]], dtype=np.float32)
    logits = np.array([[0.1, 0.9], [0.8, 0.2]], dtype=np.float32)
    xyxy = np.array([[8, 7, 12, 13], [15, 15, 25, 25]], dtype=np.float32)

    mocker.patch.object(od, "split_fields", return_value=(boxes_xywh, logits))
    mocker.patch.object(od, "logits_to_probs", return_value=logits)
    mocker.patch.object(od, "xywh_to_xyxy", return_value=xyxy)
    mocker.patch.object(od, "rescale_xyxy", return_value=xyxy)
    mocker.patch.object(od, "filter_by_conf", return_value=(xyxy, logits.max(axis=1), logits.argmax(axis=1)))
    mocker.patch.object(od.cv2.dnn, "NMSBoxes", return_value=[[0]])  # keep index 0

    preds = np.zeros((1, 6, 2), dtype=np.float32)
    dets = detector._postprocess(preds, image_shape=(480, 640))

    assert isinstance(dets, list) and len(dets) == 1
    bbox, score, label = dets[0]
    assert np.allclose(bbox, xyxy[0])
    assert np.isclose(score, 0.9)
    assert label == "class1"


def test_postprocess_no_detections(detector: od.ObjectDetector, mocker: MockerFixture) -> None:
    mocker.patch.object(od, "split_fields", return_value=(np.zeros((0, 4)), np.zeros((0, 2))))
    mocker.patch.object(od, "logits_to_probs", return_value=np.zeros((0, 2)))
    mocker.patch.object(od, "xywh_to_xyxy", return_value=np.zeros((0, 4)))
    mocker.patch.object(od, "rescale_xyxy", return_value=np.zeros((0, 4)))
    mocker.patch.object(
        od, "filter_by_conf", return_value=(np.zeros((0, 4)), np.zeros((0,)), np.zeros((0,), dtype=int))
    )

    mocker.patch.object(od.cv2.dnn, "NMSBoxes", return_value=[])

    dets = detector._postprocess(np.zeros((1, 6, 0)), image_shape=(100, 200))
    assert dets == []


def test_forward_wires_methods(
    detector: od.ObjectDetector, mocker: MockerFixture, fake_settings: SimpleNamespace
) -> None:
    pre = mocker.patch.object(detector, "_preprocess", return_value="P")
    infer = mocker.patch.object(detector, "_infer", return_value="O")
    post = mocker.patch.object(detector, "_postprocess", return_value=[(np.array([1, 2, 3, 4]), 0.9, "dog")])

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
