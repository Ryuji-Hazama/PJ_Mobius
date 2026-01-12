"""
Health check router.

Handles application health check endpoints.
"""

from fastapi import APIRouter

import BaseModelData as BMD

router = APIRouter(tags=["health"])


@router.get("/healthcheck", response_model=BMD.HealthCheckResponse)
def HealthCheck():

    return {"ResponseMessage": "Hello from PJ_Mobius."}
