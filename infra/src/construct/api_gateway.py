from pathlib import Path

from cdktf import Fn, TerraformResourceLifecycle
from cdktf_cdktf_provider_google.apikeys_key import ApikeysKey, ApikeysKeyRestrictions, ApikeysKeyRestrictionsApiTargets
from cdktf_cdktf_provider_google_beta.google_api_gateway_api import GoogleApiGatewayApi
from cdktf_cdktf_provider_google_beta.google_api_gateway_api_config import (
    GoogleApiGatewayApiConfigA,
    GoogleApiGatewayApiConfigGatewayConfig,
    GoogleApiGatewayApiConfigGatewayConfigBackendConfig,
    GoogleApiGatewayApiConfigOpenapiDocuments,
    GoogleApiGatewayApiConfigOpenapiDocumentsDocument,
)
from cdktf_cdktf_provider_google_beta.google_api_gateway_gateway import GoogleApiGatewayGateway
from cdktf_cdktf_provider_google_beta.provider import GoogleBetaProvider
from cdktf_cdktf_provider_random.id import Id
from constructs import Construct
from pydantic import BaseModel, ConfigDict

from src.construct.google_apis import GoogleCloudServiceApis, GoogleCloudServiceApisConfig
from src.construct.service_account import GoogleServiceAccount, GoogleServiceAccountConfig
from src.utils.naming_convention import get_resource_prefix, get_scoped_construct_id

PROJECT_DIR = Path(__file__).parent.parent.parent


class ApiGatewayConfig(BaseModel):
    """Api Gateway Configuration."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider: GoogleBetaProvider
    project: str
    location: str
    template_file_path: str
    api_spec_vars: dict
    name: str


class ApiGateway(Construct):
    """Api Gateway."""

    def __init__(
        self,
        scope: Construct,
        cdk_id: str,
        config: ApiGatewayConfig,
    ) -> None:
        super().__init__(scope, cdk_id)

        self.enable_service_api(config)

        service_account = GoogleServiceAccount(
            self,
            base_id := f"{cdk_id}Sa",
            config=GoogleServiceAccountConfig(
                project=config.project,
                name=Id(
                    self,
                    get_scoped_construct_id(base_id),
                    byte_length=2,
                    prefix="obj-det-apigateway-sa-",
                ).hex,
                roles=[
                    "roles/run.invoker",
                ],
            ),
        )

        self.api = GoogleApiGatewayApi(
            self,
            "ApiGatewayServiceApi",
            provider=config.provider,
            api_id=config.name,
            project=config.project,
            display_name=config.name,
        )

        ApikeysKey(
            self,
            "ApiGatewayKey",
            project=config.project,
            name=config.name,
            restrictions=ApikeysKeyRestrictions(
                api_targets=[
                    ApikeysKeyRestrictionsApiTargets(
                        service=self.api.managed_service,
                    )
                ]
            ),
        )

        self.api_config = GoogleApiGatewayApiConfigA(
            self,
            "ApiGatewayApiConfig",
            provider=config.provider,
            project=config.project,
            api=self.api.api_id,
            display_name=config.name,
            gateway_config=GoogleApiGatewayApiConfigGatewayConfig(
                backend_config=GoogleApiGatewayApiConfigGatewayConfigBackendConfig(
                    google_service_account=service_account.email
                )
            ),
            openapi_documents=[
                GoogleApiGatewayApiConfigOpenapiDocuments(
                    document=GoogleApiGatewayApiConfigOpenapiDocumentsDocument(
                        path="openapi.yaml",
                        contents=Fn.base64encode(
                            Fn.templatefile(
                                Path(config.template_file_path).as_posix(),
                                config.api_spec_vars,
                            )
                        ),
                    )
                )
            ],
            lifecycle=TerraformResourceLifecycle(
                create_before_destroy=True,
            ),
        )

        self.gateway = GoogleApiGatewayGateway(
            self,
            "ApiGatewayGateway",
            provider=config.provider,
            project=config.project,
            api_config=self.api_config.id,
            gateway_id=config.name,
            region=config.location,
        )

    def enable_service_api(self, config: ApiGatewayConfig) -> None:
        """Enable the ApiGateway API."""
        GoogleCloudServiceApis(
            self,
            "ApiGatewayApis",
            GoogleCloudServiceApisConfig(
                project=config.project,
                services=[
                    "apigateway.googleapis.com",
                    "servicemanagement.googleapis.com",
                    "servicecontrol.googleapis.com",
                    "apikeys.googleapis.com",
                ],
                disable_on_destroy=False,
            ),
        )
