"""Карточка субъекта МСП по ИНН и данные об уплаченных налогах."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Entity, TaxPayment
from ..schemas import EntityDetail, TaxPaymentOut

router = APIRouter()


@router.get("/{inn}", response_model=EntityDetail)
async def get_entity(inn: str, db: AsyncSession = Depends(get_db)):
    """Возвращает полные данные субъекта МСП по ИНН со всеми связями."""
    stmt = (
        select(Entity)
        .where(Entity.inn == inn)
        .options(
            selectinload(Entity.okved_list),
            selectinload(Entity.licenses),
            selectinload(Entity.products),
            selectinload(Entity.partnerships),
        )
    )
    result = await db.execute(stmt)
    entity = result.scalar_one_or_none()

    if entity is None:
        raise HTTPException(status_code=404, detail="Субъект МСП не найден")

    return EntityDetail.model_validate(entity)


@router.get("/{inn}/taxes", response_model=List[TaxPaymentOut])
async def get_entity_taxes(inn: str, db: AsyncSession = Depends(get_db)):
    """Возвращает данные об уплаченных налогах организации по ИНН."""
    entity = await db.execute(select(Entity).where(Entity.inn == inn))
    entity = entity.scalar_one_or_none()

    if entity is None:
        raise HTTPException(status_code=404, detail="Субъект МСП не найден")

    stmt = (
        select(TaxPayment)
        .where(TaxPayment.entity_id == entity.id)
        .order_by(TaxPayment.data_date.desc().nullslast(), TaxPayment.tax_name)
    )
    result = await db.execute(stmt)
    taxes = result.scalars().all()

    return [TaxPaymentOut.model_validate(t) for t in taxes]
