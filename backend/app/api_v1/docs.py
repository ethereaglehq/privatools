"""Mount read-only public documentation outside auth and quota dependencies."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .catalog import build_catalog
from .schema import build_schema, invalidate

router = APIRouter()
_HEADERS = {"Cache-Control": "public, max-age=0, must-revalidate", "X-Content-Type-Options": "nosniff"}


@router.get("/operations", include_in_schema=False)
async def operations(request: Request):
    return JSONResponse(await run_in_threadpool(build_catalog, request.app), headers=_HEADERS)


@router.get("/openapi.json", include_in_schema=False)
async def openapi(request: Request):
    return JSONResponse(await run_in_threadpool(build_schema, request.app), headers=_HEADERS)


def mount(app):
    """Call once after mounting the public v1 tool and optional job routers."""
    app.include_router(router, prefix="/api/v1")
    invalidate(app)
