"""Загрузка XML/ZIP файлов ФНС и просмотр истории импортов."""
import logging
import os
import uuid
from typing import List

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models import ImportLog
from ..schemas import ImportLogOut
from ..services.importer import run_import_task, run_import_zip_task
from ..services.tax_importer import run_tax_import_task, run_tax_import_zip_task

logger = logging.getLogger(__name__)

router = APIRouter()

_TAX_MARKERS = [s.encode("utf-8") for s in ["СвУплСумНал", "СведНП", "paytax"]]


def _detect_format(filepath: str) -> str:
    with open(filepath, "rb") as f:
        head = f.read(4096)
    for marker in _TAX_MARKERS:
        if marker in head:
            return "tax"
    return "msp"


@router.post("/upload")
async def upload_xml(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла не указано")

    name_lower = file.filename.lower()
    if not (name_lower.endswith(".xml") or name_lower.endswith(".zip")):
        raise HTTPException(status_code=400, detail="Допустимы только XML и ZIP файлы")

    os.makedirs(settings.upload_dir, exist_ok=True)

    safe_filename = f"{uuid.uuid4()}_{os.path.basename(file.filename)}"
    filepath = os.path.join(settings.upload_dir, safe_filename)

    async with aiofiles.open(filepath, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)

    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    fmt = _detect_format(filepath)
    fmt_label = "налоги" if fmt == "tax" else "реестр МСП"
    logger.info(
        "Файл '%s' сохранён (%s, %.1f МБ), определён формат: %s",
        file.filename, safe_filename, file_size_mb, fmt_label,
    )

    log = ImportLog(type=fmt, filename=file.filename, status="processing")
    db.add(log)
    await db.commit()
    await db.refresh(log)
    logger.info("Создана запись импорта id=%d, тип=%s", log.id, fmt)

    if name_lower.endswith(".zip"):
        task = run_tax_import_zip_task if fmt == "tax" else run_import_zip_task
        logger.info("Запуск фоновой задачи для ZIP архива, import_id=%d", log.id)
        background_tasks.add_task(task, filepath, file.filename, log.id)
    else:
        task = run_tax_import_task if fmt == "tax" else run_import_task
        logger.info("Запуск фоновой задачи для XML файла, import_id=%d", log.id)
        background_tasks.add_task(task, filepath, file.filename, log.id)

    return {"import_id": log.id, "status": "processing", "filename": file.filename}


@router.get("/imports", response_model=List[ImportLogOut])
async def get_imports(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Список последних импортов."""
    stmt = select(ImportLog).order_by(desc(ImportLog.uploaded_at)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [ImportLogOut.model_validate(log) for log in logs]


@router.get("/imports/{import_id}", response_model=ImportLogOut)
async def get_import_status(import_id: int, db: AsyncSession = Depends(get_db)):
    """Статус конкретного импорта (для polling)."""
    log = await db.get(ImportLog, import_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Импорт не найден")
    return ImportLogOut.model_validate(log)
