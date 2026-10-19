import logging
from typing import Any, Dict, List
import httpx

from config import settings

logger = logging.getLogger("bot.api_client")


class CoreApiClient:
    def __init__(self, base_url: str = settings.CORE_API_URL, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_host_status(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/v1/status")
            resp.raise_for_status()
            return resp.json()

    async def get_containers(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/v1/containers")
            resp.raise_for_status()
            return resp.json()

    async def restart_container(self, container_id: str, triggered_by: str = "telegram_bot") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/v1/containers/{container_id}/restart",
                params={"triggered_by": triggered_by},
            )
            resp.raise_for_status()
            return resp.json()

    async def stop_container(self, container_id: str, triggered_by: str = "telegram_bot") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/v1/containers/{container_id}/stop",
                params={"triggered_by": triggered_by},
            )
            resp.raise_for_status()
            return resp.json()

    async def start_container(self, container_id: str, triggered_by: str = "telegram_bot") -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/v1/containers/{container_id}/start",
                params={"triggered_by": triggered_by},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_container_logs(
        self, container_id: str, tail: int = 20, triggered_by: str = "telegram_bot"
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/v1/containers/{container_id}/logs",
                params={"tail": tail, "triggered_by": triggered_by},
            )
            resp.raise_for_status()
            return resp.json()


api_client = CoreApiClient()
