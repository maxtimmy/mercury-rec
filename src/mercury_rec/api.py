"""HTTP entrypoint for MercuryRec serving."""

from fastapi import FastAPI
from pydantic import BaseModel

from mercury_rec import __version__
from mercury_rec.config import get_settings

app = FastAPI(title="MercuryRec", version=__version__)


class HealthResponse(BaseModel):
    status: str
    environment: str
    model_version: str


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def liveness() -> HealthResponse:
    """Report whether the process is alive without external dependency checks."""

    settings = get_settings()
    return HealthResponse(
        status="ok", environment=settings.environment, model_version=settings.model_version
    )


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
def readiness() -> HealthResponse:
    """Report initial application readiness; dependencies are added in V1+."""

    return liveness()
