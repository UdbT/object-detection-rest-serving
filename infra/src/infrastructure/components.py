from pathlib import Path

from constructs import Construct

from src.config import settings
from src.construct.api_gateway import ApiGateway, ApiGatewayConfig
from src.construct.stack import Stack
from src.infrastructure.object_detection_serving.infrastructure import ObjectDetectionServing


class ObjectDetectionStack(Stack):
    """The main stack for the Object Detection application."""

    def __init__(self, scope: Construct, cdk_id: str) -> None:
        super().__init__(scope, cdk_id)

        api_runtime_dir = Path("../").resolve()

        self.object_detection_serving = ObjectDetectionServing(
            self,
            f"{self.app_name}Serving",
            location=self.region,
            project_id=self.project,
        )

        self.api_gateway = ApiGateway(
            self,
            base_id := f"{self.app_name}ApiGateway",
            config=ApiGatewayConfig(
                provider=self.google_provider_beta,
                project=self.project,
                location=self.api_gw_region,
                name=self.get_unique_name(base_id),
                template_file_path=str(api_runtime_dir / "openapi-2.0.yml"),
                api_spec_vars={
                    "cloud_run_url": self.object_detection_serving.cloud_run.uri,
                    "gateway_timeout": settings.default_api_timeout,
                },
            ),
        )
