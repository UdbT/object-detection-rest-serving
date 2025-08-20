import asyncio
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request

from src.routers.schema import DetectedObject, ObjectDetectionRequest, ObjectDetectionResponse

if TYPE_CHECKING:
    from src.models.object_detector import ObjectDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["forward"])


@router.post("/forward", responses={200: {"model": ObjectDetectionResponse}})
async def forward(input_data: ObjectDetectionRequest, request: Request) -> ObjectDetectionResponse:
    """Run object detection on the provided image.

    Args:
        input_data (ObjectDetectionRequest): Structured request including the image to be processed.
        request (Request): FastAPI request object for accessing app state (model registry).

    Returns:
        ObjectDetectionResponse: The response containing the detection results.
    """
    model: ObjectDetector = request.app.state.object_detector

    results = await asyncio.to_thread(model.forward, input_data.image)

    detections = results["detections"]
    detections = [DetectedObject(bbox=det[0], score=det[1], label=det[2]) for det in detections]

    logger.info("Detected objects count: %d", len(detections), extra={"detections": [det.model_dump() for det in detections]})
    return ObjectDetectionResponse(detections=detections)
