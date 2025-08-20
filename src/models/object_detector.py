import logging

import cv2
import numpy as np

import onnxruntime as ort

from src.config import settings
from src.utils.model_utils import filter_by_conf, logits_to_probs, rescale_xyxy, split_fields, xywh_to_xyxy
from src.utils.profiling import timeit

logger = logging.getLogger(__name__)


class ObjectDetector:
    """Class for Object Detection Model."""

    def __init__(self, model_path: str) -> None:
        """Initialize the Object Detection model.

        Args:
            model_path (str): Path to the ONNX model file.
        """
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.height, self.width = self.input_shape[2], self.input_shape[3]

        logger.info("Object Detection ONNX model has been initialized")

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the input image for the model.

        Args:
            image (np.ndarray): input image

        Returns:
            np.ndarray: preprocessed image
        """
        resized_image = cv2.resize(image, (self.width, self.height))  # Resize to model input size
        img_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        img_norm = img_rgb.astype(np.float32) / 255.0  # Normalize to [0, 1]
        img_transposed = np.transpose(img_norm, (2, 0, 1))  # HWC → CHW
        img_input = np.expand_dims(img_transposed, axis=0)
        return img_input

    def _infer(self, preprocessed_image: np.ndarray) -> np.ndarray:
        """Run inference on the input image.

        Args:
            image (np.ndarray): input image

        Returns:
            np.ndarray: model outputs
        """
        outputs = self.session.run([self.output_name], {self.input_name: preprocessed_image})[0]
        return outputs

    def _postprocess(self, preds: np.ndarray, image_shape: tuple[int, int]) -> list[tuple]:
        """Postprocess the model outputs to extract bounding boxes and class labels.

        Args:
            outputs (np.ndarray): model outputs
            image_shape (tuple[int, int]): shape of the input image

        Returns:
            list[tuple]: a list of tuples containing bounding boxes and class labels
        """
        # Split fields
        boxes, cls_logits = split_fields(preds)

        # Convert class logits -> probs
        class_probs = logits_to_probs(cls_logits)

        # Compute scores and labels
        scores = class_probs.max(axis=1)
        labels = class_probs.argmax(axis=1)

        # Convert boxes to corners in input (640x640) space
        xyxy = xywh_to_xyxy(boxes)

        # Scale back to original image size
        xyxy = rescale_xyxy(xyxy, image_shape, (self.input_shape[3], self.input_shape[2]))

        # Confidence filter
        xyxy, scores, labels = filter_by_conf(xyxy, scores, labels, settings.conf_thres)

        # Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(
            bboxes=xyxy.tolist(),
            scores=scores.tolist(),
            score_threshold=settings.conf_thres,
            nms_threshold=settings.iou_thres,
        )

        detections = []
        if len(indices) > 0:
            for i in np.array(indices).reshape(-1):
                detections.append((xyxy[i], scores[i], settings.coco_classes[int(labels[i])]))
        return detections

    @timeit
    def forward(self, input_image: np.ndarray) -> dict:
        """Run the object detection model.

        Args:
            input_image (np.ndarray): input image

        Returns:
            dict: a dictionary that includes predicted bounding boxes and class labels
        """
        preprocessed_image = self._preprocess(input_image)
        outputs = self._infer(preprocessed_image)
        detections = self._postprocess(outputs, input_image.shape[:2])
        return {"detections": detections}


# ruff: noqa
if __name__ == "__main__":
    object_detector = ObjectDetector("resources/yolo11m-sim-shape.onnx")
    test_image = cv2.imread("image.jpg")

    results = object_detector.forward(test_image)
    for bbox, score, label in results["detections"]:
        print(f"Detected {label} with confidence {score:.2f} at {bbox}")
# ruff: enable
