import logging
from contextlib import asynccontextmanager
from typing import List, Optional
import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncSession

from agent_client import agent_client
from config import settings
import crud
from database import get_db, init_db
from schemas import (
    AuditLogCreate,
    AuditLogResponse,
    ContainerActionResponse,
    ContainerInfoResponse,
    HostStatsResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("core-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Core API and database...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    logger.info("Shutting down Core API...")


app = FastAPI(
    title="Homelab Core API",
    description="Central brain, audit logger, and gateway for Homelab Control Center",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend and Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics setup
Instrumentator().instrument(app).expose(app)


@app.get("/healthz", summary="Health check endpoint")
async def healthz():
    return {"status": "ok"}


@app.get("/v1/status", response_model=HostStatsResponse, summary="Get host system metrics via agent")
async def get_status():
    try:
        data = await agent_client.get_host_stats()
        return HostStatsResponse.model_validate(data)
    except httpx.HTTPStatusError as e:
        logger.error(f"Agent error getting stats: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Agent error: {e.response.text}")
    except Exception as e:
        logger.error(f"Connection error to agent: {e}")
        raise HTTPException(status_code=502, detail=f"Could not reach agent: {str(e)}")


@app.get("/v1/containers", response_model=List[ContainerInfoResponse], summary="Get Docker containers via agent")
async def get_containers():
    try:
        data = await agent_client.get_containers()
        return [ContainerInfoResponse.model_validate(c) for c in data]
    except httpx.HTTPStatusError as e:
        logger.error(f"Agent error getting containers: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Agent error: {e.response.text}")
    except Exception as e:
        logger.error(f"Connection error to agent: {e}")
        raise HTTPException(status_code=502, detail=f"Could not reach agent: {str(e)}")


@app.post(
    "/v1/containers/{container_id}/restart",
    response_model=ContainerActionResponse,
    summary="Restart a container and record audit log",
)
async def restart_container_endpoint(
    container_id: str,
    triggered_by: str = Query(default="telegram_bot"),
    db: AsyncSession = Depends(get_db),
):
    try:
        res = await agent_client.restart_container(container_id)
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="restart_container",
                target=container_id,
                status="success",
                triggered_by=triggered_by,
                details="Container restarted successfully",
            ),
        )
        return ContainerActionResponse(
            status="success",
            container_id=container_id,
            action="restart",
            message="Container restarted successfully",
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to restart container {container_id}: {error_msg}")
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="restart_container",
                target=container_id,
                status="error",
                triggered_by=triggered_by,
                details=error_msg,
            ),
        )
        raise HTTPException(status_code=500, detail=f"Failed to restart container: {error_msg}")


@app.post(
    "/v1/containers/{container_id}/stop",
    response_model=ContainerActionResponse,
    summary="Stop a container and record audit log",
)
async def stop_container_endpoint(
    container_id: str,
    triggered_by: str = Query(default="telegram_bot"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await agent_client.stop_container(container_id)
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="stop_container",
                target=container_id,
                status="success",
                triggered_by=triggered_by,
                details="Container stopped successfully",
            ),
        )
        return ContainerActionResponse(
            status="success",
            container_id=container_id,
            action="stop",
            message="Container stopped successfully",
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to stop container {container_id}: {error_msg}")
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="stop_container",
                target=container_id,
                status="error",
                triggered_by=triggered_by,
                details=error_msg,
            ),
        )
        raise HTTPException(status_code=500, detail=f"Failed to stop container: {error_msg}")


@app.post(
    "/v1/containers/{container_id}/start",
    response_model=ContainerActionResponse,
    summary="Start a container and record audit log",
)
async def start_container_endpoint(
    container_id: str,
    triggered_by: str = Query(default="telegram_bot"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await agent_client.start_container(container_id)
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="start_container",
                target=container_id,
                status="success",
                triggered_by=triggered_by,
                details="Container started successfully",
            ),
        )
        return ContainerActionResponse(
            status="success",
            container_id=container_id,
            action="start",
            message="Container started successfully",
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to start container {container_id}: {error_msg}")
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="start_container",
                target=container_id,
                status="error",
                triggered_by=triggered_by,
                details=error_msg,
            ),
        )
        raise HTTPException(status_code=500, detail=f"Failed to start container: {error_msg}")


@app.get(
    "/v1/containers/{container_id}/logs",
    summary="Fetch container logs and record audit log",
)
async def get_logs_endpoint(
    container_id: str,
    tail: int = Query(default=20, ge=1, le=500),
    triggered_by: str = Query(default="telegram_bot"),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await agent_client.get_container_logs(container_id, tail=tail)
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="get_logs",
                target=container_id,
                status="success",
                triggered_by=triggered_by,
                details=f"Fetched {tail} lines of logs",
            ),
        )
        return data
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to get logs for {container_id}: {error_msg}")
        await crud.create_audit_log(
            db,
            AuditLogCreate(
                action="get_logs",
                target=container_id,
                status="error",
                triggered_by=triggered_by,
                details=error_msg,
            ),
        )
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {error_msg}")


@app.get(
    "/v1/audit",
    response_model=List[AuditLogResponse],
    summary="Get recent audit logs from database",
)
async def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    records = await crud.get_recent_audit_logs(db, limit=limit)
    return [AuditLogResponse.model_validate(r) for r in records]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.CORE_API_PORT, reload=False)
