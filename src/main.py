import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.models.object_detector import ObjectDetector
from src.routers import health_check
from src.routers.v1 import forward
from src.utils.logger import setup_log
from src.utils.middleware import RequestIDMiddleware

setup_log()
logger = logging.getLogger(__name__)

ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Manages the startup and shutdown events for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app.state.object_detector = ObjectDetector(settings.model_path)

    logger.info("Finished initializing models.")
    yield


app = FastAPI(lifespan=lifespan)
app.title = "Object Detection Serving"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=ALLOW_METHODS,
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.include_router(health_check.router)
app.include_router(forward.router)
