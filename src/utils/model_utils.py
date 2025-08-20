import numpy as np


def sigmoid(mat: np.ndarray) -> np.ndarray:
    """Apply sigmoid activation function to a numpy array.

    Args:
        mat (np.ndarray): Input array.

    Returns:
        np.ndarray: Sigmoid activated array.
    """
    return 1.0 / (1.0 + np.exp(-mat))


def xywh_to_xyxy(boxes: np.ndarray) -> np.ndarray:
    """Convert bounding boxes from [x,y,w,h] format to [x1,y1,x2,y2] format.

    Args:
        boxes (np.ndarray): Bounding boxes in [x,y,w,h] format.

    Returns:
            np.ndarray: Bounding boxes in [x1,y1,x2,y2] format.
    """
    # boxes: (N,4) -> [x,y,w,h] (center format) -> [x1,y1,x2,y2]
    x, y, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    x1 = x - w / 2.0
    y1 = y - h / 2.0
    x2 = x + w / 2.0
    y2 = y + h / 2.0
    return np.stack([x1, y1, x2, y2], axis=1)


def split_fields(preds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split the model predictions into bounding boxes and class logits.

    Args:
        preds (np.ndarray): Model predictions.

    Returns:
        tuple[np.ndarray, np.ndarray]: Bounding boxes and class logits.
    """
    p = np.squeeze(preds, 0).transpose(1, 0)
    return p[:, :4], p[:, 4:]


def logits_to_probs(cls_logits: np.ndarray) -> np.ndarray:
    """Convert class logits to probabilities using sigmoid activation.

    Args:
        cls_logits (np.ndarray): Class logits.

    Returns:
        np.ndarray: Class probabilities.
    """
    if 0.0 <= cls_logits.min() <= cls_logits.max() <= 1.0:
        return cls_logits
    return sigmoid(cls_logits)


def rescale_xyxy(xyxy: np.ndarray, image_shape: tuple[int, int], input_shape: tuple[int, int]) -> np.ndarray:
    """Rescale bounding boxes from input image size to original image size.

    Args:
        xyxy (np.ndarray): Bounding boxes in [x1,y1,x2,y2] format.
        image_shape (tuple[int, int]): Shape of the original image (height, width).
        input_shape (tuple[int, int]): Shape of the input image (height, width).

    Returns:
        np.ndarray: Rescaled bounding boxes in [x1,y1,x2,y2] format.
    """
    img_h, img_w = image_shape
    sx = img_w / float(input_shape[1])
    sy = img_h / float(input_shape[0])
    out = xyxy.copy()
    out[:, [0, 2]] *= sx
    out[:, [1, 3]] *= sy
    return out


def filter_by_conf(
    xyxy: np.ndarray, scores: np.ndarray, labels: np.ndarray, thres: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Filter detections by confidence threshold.

    Args:
        xyxy (np.ndarray): Bounding boxes in [x1,y1,x2,y2] format.
        scores (np.ndarray): Confidence scores.
        labels (np.ndarray): Class labels.
        thres (float): Confidence threshold.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: Filtered bounding boxes, scores, and labels.
    """
    mark = scores >= thres
    return xyxy[mark], scores[mark], labels[mark]
