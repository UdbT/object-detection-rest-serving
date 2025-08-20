from pathlib import Path

from cdktf_cdktf_provider_random.id import Id
from constructs import Construct

from src.config import settings
from src.construct.cloud_run import GoogleCloudRun, GoogleCloudRunConfig
from src.construct.service_account import GoogleServiceAccount, GoogleServiceAccountConfig
from src.utils.naming_convention import get_scoped_construct_id


class ObjectDetectionServing(Construct):
    """Construct contains resources for Object Detection API."""

    def __init__(  # noqa: PLR0913 Too many arguments
        self,
        scope: Construct,
        cdk_id: str,
        *,
        location: str,
        project_id: str,
    ) -> None:
        super().__init__(scope, cdk_id)

        service_account = GoogleServiceAccount(
            self,
            base_id := f"{cdk_id}Sa",
            config=GoogleServiceAccountConfig(
                project=project_id,
                name=Id(
                    self,
                    get_scoped_construct_id(base_id),
                    byte_length=2,
                    prefix="obj-detect-serving-sa-",
                ).hex,
                roles=[
                    "roles/viewer",
                    "roles/logging.logWriter",
                ],
            ),
        )

        object_detection_api_cloud_run_config = GoogleCloudRunConfig(
            project=project_id,
            location=location,
            docker_image=settings.cloud_run_configs.object_detection_serving.image,
            container_port=settings.cloud_run_configs.object_detection_serving.container_port,
            cpu=settings.cloud_run_configs.object_detection_serving.cpu,
            memory=settings.cloud_run_configs.object_detection_serving.memory,
            cpu_idle=settings.cloud_run_configs.object_detection_serving.cpu_idle,
            startup_cpu_boost=settings.cloud_run_configs.object_detection_serving.startup_cpu_boost,
            service_account=service_account.email,
            protocol=GoogleCloudRunConfig.Protocol.http1,
            execution_environment=GoogleCloudRunConfig.ExecutionEnv.gen2,
            environment_variables={
                "ENV_FOR_DYNACONF": settings.env_for_dynaconf,
            },
        )

        self.cloud_run = GoogleCloudRun(
            self, cdk_id, object_detection_api_cloud_run_config
        ).cloud_run
