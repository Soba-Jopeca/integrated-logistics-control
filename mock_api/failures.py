"""Falhas deliberadas de transporte/formato, separadas dos eventos de negocio."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/scenarios", tags=["Falhas controladas"])


@router.get("/delay", summary="Resposta atrasada; timeout depende do cliente")
async def delay(seconds: Annotated[float, Query(ge=0.1, le=2.0)] = 1.0):
    await asyncio.sleep(seconds)
    return {"scenario": "delay", "delay_seconds": seconds}


@router.get(
    "/http-503", responses={503: {"description": "Indisponibilidade HTTP simulada"}}
)
def http_503():
    return JSONResponse(
        status_code=503,
        content={"scenario": "http_503", "error": "SIMULATED_UNAVAILABLE"},
        headers={"X-ILC-Scenario": "http_503"},
    )


@router.get("/invalid-json", response_class=Response)
def invalid_json():
    return Response(
        content='{"scenario":"invalid_json",',
        status_code=200,
        media_type="application/json",
        headers={"X-ILC-Scenario": "invalid_json"},
    )
