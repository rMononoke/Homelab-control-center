from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    action: str
    target: str
    status: str
    triggered_by: str = "system"
    details: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime


class HostStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_free_gb: float
    disk_total_gb: float
    uptime_seconds: int


class ContainerInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    short_id: str
    name: str
    status: str
    image: str
    state: str


class ContainerActionResponse(BaseModel):
    status: str
    container_id: str
    action: str
    message: Optional[str] = None
