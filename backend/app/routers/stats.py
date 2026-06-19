"""Статистика реестра."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Entity, ImportLog, TaxPayment
from ..schemas import StatsOut

router = APIRouter()


@router.get("/stats", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Общая статистика по реестру."""
    total = (await db.execute(select(func.count(Entity.id)))).scalar_one()
    total_ip = (
        await db.execute(
            select(func.count(Entity.id)).where(Entity.entity_type == "IP")
        )
    ).scalar_one()
    total_org = (
        await db.execute(
            select(func.count(Entity.id)).where(Entity.entity_type == "ORG")
        )
    ).scalar_one()
    total_tax_records = (
        await db.execute(select(func.count(TaxPayment.id)))
    ).scalar_one()
    last_import = (
        await db.execute(
            select(func.max(ImportLog.uploaded_at)).where(
                ImportLog.status == "completed"
            )
        )
    ).scalar_one()

    return StatsOut(
        total_entities=total,
        total_ip=total_ip,
        total_org=total_org,
        total_tax_records=total_tax_records,
        last_import=last_import,
    )
