import re

from cdktf_cdktf_provider_google.project_iam_member import ProjectIamMember
from cdktf_cdktf_provider_google.service_account import ServiceAccount
from constructs import Construct
from inflection import camelize, dasherize, underscore
from pydantic import BaseModel

from src.construct.google_apis import GoogleCloudServiceApis, GoogleCloudServiceApisConfig


class GoogleServiceAccountConfig(BaseModel):
    """Service Account Configuration."""

    project: str
    name: str
    roles: list[str]


class GoogleServiceAccount(Construct):
    """Service Account Construct."""

    def __init__(
        self,
        scope: Construct,
        cdk_id: str,
        config: GoogleServiceAccountConfig,
    ) -> None:
        super().__init__(scope, cdk_id)

        self.service_account = ServiceAccount(
            self,
            cdk_id,
            account_id=config.name,
            display_name=dasherize(underscore(cdk_id)),
        )

        for role in config.roles:
            ProjectIamMember(
                self,
                f"{cdk_id}{camelize(re.sub(r"\W", "_", role))}",
                member=self.service_account.member,
                project=config.project,
                role=role,
            )

    def enable_service_api(self, config: GoogleServiceAccountConfig) -> None:
        """Enable the IAM API."""
        GoogleCloudServiceApis(
            self,
            "ArtifactRegistryApi",
            GoogleCloudServiceApisConfig(
                project=config.project,
                services=["iam.googleapis.com"],
                disable_on_destroy=False,
            ),
        )

    @property
    def email(self) -> str:
        """Get the E-mail of the Service Account.

        Returns:
            str: The E-mail of the Service Account.
        """
        return self.service_account.email
