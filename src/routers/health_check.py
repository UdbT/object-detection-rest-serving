from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get(
    "/health_check",
    responses={
        200: {
            "description": "Successful health check",
        }
    },
    summary="Health Check",
)
async def healthcheck() -> JSONResponse:
    """Health check endpoint.

    Returns:
        JSONResponse: 200 status
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "OK"},
    )
