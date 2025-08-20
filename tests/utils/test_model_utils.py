from unittest.mock import patch

import numpy as np
import pytest

from src.utils.model_utils import (
    filter_by_conf,
    logits_to_probs,
    rescale_xyxy,
    sigmoid,
    split_fields,
    xywh_to_xyxy,
)


@pytest.mark.parametrize(
    "x,expected",
    [
        (np.array([0.0]), np.array([0.5])),
        (np.array([-np.inf, 0.0, np.inf]), np.array([0.0, 0.5, 1.0])),
        (np.array([-2.0, 2.0]), 1.0 / (1.0 + np.exp(np.array([2.0, -2.0])))),
    ],
)
def test_sigmoid_values(x, expected):
    out = sigmoid(x)
    assert out.shape == x.shape
    assert np.allclose(out, expected, atol=1e-7)
    assert np.all((out >= 0.0) & (out <= 1.0))


def test_xywh_to_xyxy():
    boxes = np.array(
        [
            [10.0, 10.0, 4.0, 6.0],  # x,y,w,h
            [0.0, 0.0, 2.0, 2.0],
            [5.0, 7.0, 0.0, 0.0],  # zero-size box
        ],
        dtype=np.float32,
    )
    out = xywh_to_xyxy(boxes)
    expected = np.array(
        [
            [8.0, 7.0, 12.0, 13.0],
            [-1.0, -1.0, 1.0, 1.0],
            [5.0, 7.0, 5.0, 7.0],
        ],
        dtype=np.float32,
    )

    assert out.shape == (3, 4)
    assert np.allclose(out, expected, atol=1e-6)


def test_split_fields_shapes_and_values():
    boxes_true = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.float32)  # (N,4)
    logits_true = np.array([[0.1, 0.2, 0.3], [3.0, -1.0, 0.0]], dtype=np.float32)  # (N, C=3)
    p = np.concatenate([boxes_true, logits_true], axis=1)  # (N, 7)
    preds = p.T[None, ...]  # (1, 7, 2)

    boxes, logits = split_fields(preds)

    assert boxes.shape == (2, 4)
    assert logits.shape == (2, 3)
    assert np.allclose(boxes, boxes_true)
    assert np.allclose(logits, logits_true)


def test_logits_to_probs_passthrough_when_in_01():
    probs = np.array([[0.0, 0.2], [0.8, 1.0]], dtype=np.float32)
    out = logits_to_probs(probs.copy())

    # Must be returned as-is
    assert np.all(out is not probs) or np.allclose(out, probs)  # value-wise equal
    assert np.allclose(out, probs)


@pytest.mark.parametrize(
    "logits",
    [
        np.array([[-2.0, 0.0, 2.0]], dtype=np.float64),
        np.array([[10.0, -10.0, 1.5], [0.0, 0.0, 0.0]], dtype=np.float32),
    ],
)
def test_logits_to_probs_applies_sigmoid(logits):
    # Spy on sigmoid to check if it's called
    with patch("src.utils.model_utils.sigmoid") as mock_sigmoid:
        logits_to_probs(logits)
        assert mock_sigmoid.called, "sigmoid should be called"


@pytest.mark.parametrize(
    "image_shape,input_shape,boxes,expected",
    [
        # Simple 2x upscale in both dims
        (
            (200, 300),  # H,W (image)
            (100, 150),  # H,W (input)
            np.array([[1, 2, 3, 4]], dtype=np.float32),
            np.array([[2, 4, 6, 8]], dtype=np.float32),
        ),
        # Non-uniform scale
        (
            (1080, 1920),
            (640, 1280),
            np.array([[10, 20, 30, 40], [0, 0, 100, 100]], dtype=np.float32),
            np.array(
                [
                    [10 * (1920 / 1280.0), 20 * (1080 / 640.0), 30 * (1920 / 1280.0), 40 * (1080 / 640.0)],
                    [0, 0, 100 * (1920 / 1280.0), 100 * (1080 / 640.0)],
                ],
                dtype=np.float32,
            ),
        ),
    ],
)
def test_rescale_xyxy(image_shape, input_shape, boxes, expected):
    out = rescale_xyxy(boxes, image_shape, input_shape)
    assert np.allclose(out, expected, atol=1e-6)


def test_filter_by_conf_inclusive_threshold():
    xyxy = np.array([[0, 0, 10, 10], [1, 1, 5, 5], [2, 2, 3, 3]], dtype=np.float32)
    scores = np.array([0.4, 0.5, 0.5000001], dtype=np.float32)
    labels = np.array([1, 2, 3], dtype=np.int64)

    thres = 0.5
    f_boxes, f_scores, f_labels = filter_by_conf(xyxy, scores, labels, thres)

    assert f_boxes.shape == (2, 4)
    assert np.allclose(f_scores, [0.5, 0.5000001])
    assert np.all(f_labels == np.array([2, 3]))
    assert np.allclose(f_boxes, np.array([[1, 1, 5, 5], [2, 2, 3, 3]], dtype=np.float32))


def test_filter_by_conf_all_filtered_out():
    xyxy = np.array([[0, 0, 1, 1]], dtype=np.float32)
    scores = np.array([0.1], dtype=np.float32)
    labels = np.array([0], dtype=np.int64)
    b, s, l = filter_by_conf(xyxy, scores, labels, thres=0.5)

    assert b.size == 0 and s.size == 0 and l.size == 0
    assert b.shape == (0, 4)  # preserves 2D shape for boxes
