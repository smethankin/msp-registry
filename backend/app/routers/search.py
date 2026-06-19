"""Поиск по реестру МСП."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Entity
from ..schemas import EntityCard, SearchResult

router = APIRouter()


@router.get("/search", response_model=SearchResult)
async def search(
    q: str = Query(..., min_length=1, description="ФИО, ИНН, ОГРН или название"),
    type: Optional[str] = Query(None, description="Фильтр: 'ip' или 'org'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Поиск по ИНН/ОГРН (если q состоит только из цифр), либо
    full-text search по русскому индексу с LIKE fallback.
    """
    q_clean = q.strip()

    base = select(Entity)
    count_base = select(func.count()).select_from(Entity)

    conditions = []

    if q_clean.isdigit():
        # Точный поиск по ИНН или ОГРН
        conditions.append(or_(Entity.inn == q_clean, Entity.ogrn == q_clean))
    else:
        # FTS по русскому индексу + ILIKE fallback
        fts = text(
            "to_tsvector('russian', coalesce(full_name,'') || ' ' || coalesce(short_name,'')) "
            "@@ plainto_tsquery('russian', :q)"
        ).bindparams(q=q_clean)
        like_pattern = f"%{q_clean}%"
        conditions.append(
            or_(
                fts,
                Entity.full_name.ilike(like_pattern),
                Entity.short_name.ilike(like_pattern),
            )
        )

    if type:
        type_upper = type.upper()
        if type_upper in ("IP", "ORG"):
            conditions.append(Entity.entity_type == type_upper)

    for cond in conditions:
        base = base.where(cond)
        count_base = count_base.where(cond)

    # Получаем total
    total_result = await db.execute(count_base)
    total = total_result.scalar_one()

    # Получаем страницу
    offset = (page - 1) * page_size
    stmt = base.order_by(Entity.id).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    entities = result.scalars().all()

    return SearchResult(
        total=total,
        page=page,
        page_size=page_size,
        items=[EntityCard.model_validate(e) for e in entities],
    )
