import argparse
import json
from pathlib import Path

import yaml
from fastapi.openapi.utils import get_openapi
from fastapi_swagger2 import FastAPISwagger2

from src.config import settings
from src.main import app


def get_swagger_v3(output_dir: str, version: str) -> None:
    """Generate HTML swagger page from Fastapi app.

    Args:
        output_dir (str): Output path
        version (str): API version
    """
    with open(Path(output_dir) / "openapi.json", "w") as f:
        json.dump(
            get_openapi(
                title=app.title,
                version=version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
            ),
            f,
        )


def get_swagger_v2(output_dir: str, version: str, cloud_run_url: str, gateway_timeout: str) -> None:
    """Generate openapi-2.0.yml file for GCP API Gateway.

    Args:
        output_dir (str): Output path
        version (str): API version
        cloud_run_url (str): Cloud Run URL
        gateway_timeout (str): API Gateway Timeout in second
    """
    FastAPISwagger2(app)
    spec = app.swagger2()

    spec["info"]["version"] = version
    spec["info"]["contact"] = {}
    spec["x-google-backend"] = {"address": cloud_run_url, "deadline": gateway_timeout}
    spec["basePath"] = "/"
    spec["securityDefinitions"] = {"APIKey": {"type": "apiKey", "in": "header", "name": "x-api-key"}}
    spec["schemes"] = ["https"]
    spec["consumes"] = ["application/json"]
    spec["produces"] = ["application/json"]
    spec["security"] = [{"APIKey": []}]

    # modify openapi to be complied with gcp api gateway
    for _definition_name, definition in spec.get("definitions", {}).items():
        # correct "examples" with "example"
        examples = definition.pop("examples", None)
        if examples:
            definition["example"] = examples

        # remove unsupported "prefixItems" from each property
        properties = definition.get("properties", {})
        for _prop_name, prop_details in properties.items():
            prop_details.pop("prefixItems", None)

    with open(Path(output_dir) / "openapi-2.0.yml", "w") as f:
        yaml.dump(spec, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default=".")
    parser.add_argument("--version", type=str, default="0.1.0")
    args, _ = parser.parse_known_args()

    # generate openapi.json
    get_swagger_v3(args.output_dir, args.version)

    # generate openapi-2.0.yml
    get_swagger_v2(
        args.output_dir,
        args.version,
        settings.get("cloud_run_url", r"${cloud_run_url}"),
        settings.get("gateway_timeout", r"${gateway_timeout}"),
    )
