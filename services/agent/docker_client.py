import asyncio
import logging
from typing import List, Optional
import docker
from docker.errors import DockerException, NotFound
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class ContainerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    short_id: str
    name: str
    status: str
    image: str
    state: str


def _get_docker_client() -> docker.DockerClient:
    return docker.from_env()


def _sync_list_containers() -> List[ContainerInfo]:
    client = _get_docker_client()
    raw_containers = client.containers.list(all=True)
    result = []
    for c in raw_containers:
        # Safely extract image name without triggering unhandled 404 from c.image
        image_tag = c.attrs.get("Config", {}).get("Image")
        if not image_tag:
            try:
                if c.image and c.image.tags:
                    image_tag = c.image.tags[0]
            except Exception:
                raw_img = str(c.attrs.get("Image", "unknown"))
                image_tag = raw_img.split(":")[-1][:12] if ":" in raw_img else raw_img[:12]

        if not image_tag:
            image_tag = "unknown"

        result.append(
            ContainerInfo(
                id=c.id,
                short_id=c.short_id,
                name=c.name.lstrip("/"),
                status=c.status,
                image=image_tag,
                state=c.attrs.get("State", {}).get("Status", c.status),
            )
        )
    return result


def _sync_restart_container(container_id: str) -> bool:
    client = _get_docker_client()
    container = client.containers.get(container_id)
    container.restart()
    return True


def _sync_stop_container(container_id: str) -> bool:
    client = _get_docker_client()
    container = client.containers.get(container_id)
    container.stop()
    return True


def _sync_start_container(container_id: str) -> bool:
    client = _get_docker_client()
    container = client.containers.get(container_id)
    container.start()
    return True


def _sync_get_container_logs(container_id: str, tail: int = 20) -> str:
    client = _get_docker_client()
    container = client.containers.get(container_id)
    raw_logs = container.logs(tail=tail, stdout=True, stderr=True)
    if isinstance(raw_logs, bytes):
        return raw_logs.decode("utf-8", errors="replace")
    return str(raw_logs)


async def list_containers() -> List[ContainerInfo]:
    return await asyncio.to_thread(_sync_list_containers)


async def restart_container(container_id: str) -> bool:
    return await asyncio.to_thread(_sync_restart_container, container_id)


async def stop_container(container_id: str) -> bool:
    return await asyncio.to_thread(_sync_stop_container, container_id)


async def start_container(container_id: str) -> bool:
    return await asyncio.to_thread(_sync_start_container, container_id)


async def get_container_logs(container_id: str, tail: int = 20) -> str:
    return await asyncio.to_thread(_sync_get_container_logs, container_id, tail)
