import logging
from contextlib import asynccontextmanager
from typing import List
from docker.errors import DockerException, NotFound
from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from docker_client import (
    ContainerInfo,
    get_container_logs,
    list_containers,
    restart_container,
    start_container,
    stop_container,
)
from system_info import SystemStats, get_system_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Homelab Agent...")
    yield
    logger.info("Shutting down Homelab Agent...")


app = FastAPI(
    title="Homelab Agent",
    description="Agent microservice for host and docker operations",
    version="1.0.0",
    lifespan=lifespan,
)

# Prometheus metrics setup
Instrumentator().instrument(app).expose(app)


@app.get("/healthz", summary="Health check endpoint")
async def healthz():
    return {"status": "ok"}


@app.get("/api/host/stats", response_model=SystemStats, summary="Get host system statistics")
async def host_stats():
    try:
        return await get_system_stats()
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/containers", response_model=List[ContainerInfo], summary="Get list of Docker containers")
async def containers():
    try:
        return await list_containers()
    except DockerException as e:
        logger.error(f"Docker API error: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@app.post("/api/containers/{container_id}/restart", summary="Restart Docker container")
async def restart_container_endpoint(container_id: str):
    try:
        await restart_container(container_id)
        return {"status": "success", "container_id": container_id, "action": "restart"}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_id}' not found")
    except DockerException as e:
        logger.error(f"Failed to restart container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@app.post("/api/containers/{container_id}/stop", summary="Stop Docker container")
async def stop_container_endpoint(container_id: str):
    try:
        await stop_container(container_id)
        return {"status": "success", "container_id": container_id, "action": "stop"}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_id}' not found")
    except DockerException as e:
        logger.error(f"Failed to stop container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@app.post("/api/containers/{container_id}/start", summary="Start Docker container")
async def start_container_endpoint(container_id: str):
    try:
        await start_container(container_id)
        return {"status": "success", "container_id": container_id, "action": "start"}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_id}' not found")
    except DockerException as e:
        logger.error(f"Failed to start container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


@app.get("/api/containers/{container_id}/logs", summary="Get Docker container logs")
async def container_logs(container_id: str, tail: int = Query(default=20, ge=1, le=500)):
    try:
        logs = await get_container_logs(container_id, tail=tail)
        return {"status": "success", "container_id": container_id, "tail": tail, "logs": logs}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{container_id}' not found")
    except DockerException as e:
        logger.error(f"Failed to get logs for container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.AGENT_PORT, reload=False)
