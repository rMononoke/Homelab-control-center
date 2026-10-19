from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditLog
from schemas import AuditLogCreate


async def create_audit_log(session: AsyncSession, log_in: AuditLogCreate) -> AuditLog:
    db_obj = AuditLog(**log_in.model_dump())
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_recent_audit_logs(session: AsyncSession, limit: int = 50) -> List[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    result = await session.scalars(stmt)
    return list(result.all())
