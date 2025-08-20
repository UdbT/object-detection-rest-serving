from cdktf_cdktf_provider_google.project_service import ProjectService
from constructs import Construct
from pydantic import BaseModel


class GoogleCloudServiceApisConfig(BaseModel):
    """Google Service apis config."""

    project: str
    services: list[str]
    disable_on_destroy: bool


class GoogleCloudServiceApis(Construct):
    """Google Service Apis. Used to enable or disable Google Cloud services."""

    def __init__(self, scope: Construct, cdk_id: str, config: GoogleCloudServiceApisConfig) -> None:
        super().__init__(scope, cdk_id)

        for idx, service in enumerate(config.services):
            ProjectService(
                self,
                f"GoogleApis{idx}",
                project=config.project,
                service=service,
                disable_on_destroy=config.disable_on_destroy,
            )
