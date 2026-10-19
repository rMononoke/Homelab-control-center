import asyncio
import time
from typing import Any, Dict
import psutil
from pydantic import BaseModel, ConfigDict


class SystemStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_free_gb: float
    disk_total_gb: float
    uptime_seconds: int


def _collect_sync_system_stats() -> Dict[str, Any]:
    # Non-blocking cpu_percent
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    boot_time = psutil.boot_time()
    uptime = int(time.time() - boot_time)

    return {
        "cpu_percent": round(cpu, 1),
        "memory_percent": round(mem.percent, 1),
        "memory_used_gb": round(mem.used / (1024**3), 2),
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "disk_percent": round(disk.percent, 1),
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "uptime_seconds": uptime,
    }


async def get_system_stats() -> SystemStats:
    """Collects host stats asynchronously without blocking the event loop."""
    raw_stats = await asyncio.to_thread(_collect_sync_system_stats)
    return SystemStats.model_validate(raw_stats)
