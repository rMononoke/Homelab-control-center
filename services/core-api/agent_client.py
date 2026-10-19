import logging
from typing import Any, Dict, List
import httpx

from config import settings

logger = logging.getLogger(__name__)


class AgentClient:
    def __init__(self, base_url: str = settings.AGENT_URL, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_host_stats(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/api/host/stats")
            resp.raise_for_status()
            return resp.json()

    async def get_containers(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/api/containers")
            resp.raise_for_status()
            return resp.json()

    async def restart_container(self, container_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/containers/{container_id}/restart")
            resp.raise_for_status()
            return resp.json()

    async def stop_container(self, container_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/containers/{container_id}/stop")
            resp.raise_for_status()
            return resp.json()

    async def start_container(self, container_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/api/containers/{container_id}/start")
            resp.raise_for_status()
            return resp.json()

    async def get_container_logs(self, container_id: str, tail: int = 20) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/api/containers/{container_id}/logs",
                params={"tail": tail},
            )
            resp.raise_for_status()
            return resp.json()


agent_client = AgentClient()
