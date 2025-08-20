import os
from pathlib import Path

from cdktf import GcsBackend, TerraformStack
from cdktf_cdktf_provider_google.provider import GoogleProvider
from cdktf_cdktf_provider_google_beta.provider import GoogleBetaProvider
from cdktf_cdktf_provider_null.provider import NullProvider
from cdktf_cdktf_provider_random.id import Id
from cdktf_cdktf_provider_random.provider import RandomProvider
from constructs import Construct

from src.config import settings
from src.utils.naming_convention import get_resource_prefix, get_scoped_construct_id


class Stack(TerraformStack):
    """A CDKTF base stack."""

    def __init__(self, scope: Construct, cdk_id: str) -> None:
        super().__init__(scope, cdk_id)

        self.project = settings.cloud_project.id
        self.region = settings.cloud_project.region
        self.api_gw_region = settings.cloud_project.api_gw.region
        self.zone = settings.cloud_project.zone
        self.env = str(settings.env_for_dynaconf).lower()
        self.app_name = settings.app_name

        GcsBackend(
            self,
            bucket=settings.backend_config.state_bucket,
            prefix=str(Path(settings.backend_config.state_prefix) / self.env / cdk_id),
            # Need to enable IAM Service Account Credentials API in application GCP project for impersonation.
            impersonate_service_account=None
            if "GITLAB_CI" in os.environ
            else settings.backend_config.impersonate_service_account,
        )

        self.google_provider = GoogleProvider(
            self,
            id="GoogleProvider",
            project=self.project,
            region=self.region,
            zone=self.zone,
        )

        self.google_provider_beta = GoogleBetaProvider(
            self,
            id="GoogleProviderBeta",
            project=self.project,
            region=self.region,
            zone=self.zone,
        )

        RandomProvider(
            self,
            id="RandomProvider",
        )

        NullProvider(self, id="NullProvider")


    def get_unique_name(self, name: str) -> str:
        """Generates a unique, hexadecimal identifier based on the provided name.

        Args:
            name (str): The base name in Camel case used to generate the unique identifier.

        Returns:
            str: A unique, hexadecimal string representing the scoped ID.
        """
        return Id(
            self,
            get_scoped_construct_id(name),
            byte_length=8,
            prefix=get_resource_prefix(name),
        ).hex
