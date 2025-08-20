from enum import StrEnum
from typing import Any, Optional

from cdktf_cdktf_provider_google.cloud_run_v2_service import (
    CloudRunV2Service,
    CloudRunV2ServiceTemplate,
    CloudRunV2ServiceTemplateContainers,
    CloudRunV2ServiceTemplateContainersEnv,
    CloudRunV2ServiceTemplateContainersPorts,
    CloudRunV2ServiceTemplateContainersResources,
    CloudRunV2ServiceTemplateScaling,
)
from cdktf_cdktf_provider_random.id import Id
from constructs import Construct
from pydantic import BaseModel

from src.config import settings
from src.construct.google_apis import GoogleCloudServiceApis, GoogleCloudServiceApisConfig
from src.utils.naming_convention import get_resource_prefix, get_scoped_construct_id


class GoogleCloudRunConfig(BaseModel):
    """Google Cloud Run configuration."""

    class Protocol(StrEnum):
        """Cloud Run Potocol Options."""

        http1 = "http1"
        http2 = "h2c"

    class ExecutionEnv(StrEnum):
        """Cloud Run Execution Environment Options."""

        gen1 = "EXECUTION_ENVIRONMENT_GEN1"
        gen2 = "EXECUTION_ENVIRONMENT_GEN2"

    project: str
    location: str
    docker_image: str
    container_port: int
    cpu: float
    memory: str
    cpu_idle: bool
    startup_cpu_boost: bool
    service_account: str | None
    protocol: Protocol
    execution_environment: Optional[ExecutionEnv] = None
    environment_variables: Optional[dict[str, Any]] = {}
    timeout: Optional[int] = settings.default_api_timeout
    min_instance_count: Optional[int] = settings.cloud_run_configs.default_min_instance_count
    max_instance_count: Optional[int] = settings.cloud_run_configs.default_max_instance_count

    class Config:
        """Model config."""

        arbitrary_types_allowed = True


class GoogleCloudRun(Construct):
    """Google Cloud Run."""

    def __init__(
        self,
        scope: Construct,
        cdk_id: str,
        config: GoogleCloudRunConfig,
        depends_on: list | None = None,
    ) -> None:
        super().__init__(scope, cdk_id)

        self.enable_service_api(config)
        self.cloud_run = CloudRunV2Service(
            self,
            base_id := cdk_id,
            location=config.location,
            name=Id(
                self,
                get_scoped_construct_id(base_id),
                byte_length=8,
                prefix=get_resource_prefix(base_id),
            ).hex,
            ingress="INGRESS_TRAFFIC_ALL",
            template=CloudRunV2ServiceTemplate(
                containers=[
                    CloudRunV2ServiceTemplateContainers(
                        image=config.docker_image,
                        resources=CloudRunV2ServiceTemplateContainersResources(
                            cpu_idle=config.cpu_idle,
                            limits={"cpu": str(config.cpu), "memory": config.memory},
                            startup_cpu_boost=config.startup_cpu_boost,
                        ),
                        ports=CloudRunV2ServiceTemplateContainersPorts(
                            name=config.protocol, container_port=config.container_port
                        ),
                        env=[
                            CloudRunV2ServiceTemplateContainersEnv(name=k, value=v)
                            for k, v in config.environment_variables.items()
                        ],
                    )
                ],
                scaling=CloudRunV2ServiceTemplateScaling(
                    min_instance_count=config.min_instance_count, max_instance_count=config.max_instance_count
                ),
                timeout=f"{config.timeout}s",
                execution_environment=config.execution_environment,
                service_account=config.service_account,
                max_instance_request_concurrency=80,
            ),
            depends_on=depends_on,
        )

    @property
    def name(self) -> str:
        """Get the name of the Cloud Run.

        Returns:
            str: The name of the Cloud Run.
        """
        return self.cloud_run.name

    @property
    def uri(self) -> str:
        """Get the URI of the Cloud Run.

        Returns:
            str: The URI of the Cloud Run.
        """
        return self.cloud_run.uri

    def enable_service_api(self, config: GoogleCloudRunConfig) -> None:
        """Enable the Cloud Run Service API."""
        GoogleCloudServiceApis(
            self,
            "CloudRunApi",
            GoogleCloudServiceApisConfig(
                project=config.project,
                services=["run.googleapis.com"],
                disable_on_destroy=False,
            ),
        )
