"""
Импортёр XML файлов ФНС с данными об уплаченных налогах.

Привязывает записи к entities по ИНН. Использует upsert по
(entity_id, doc_id, tax_name) для избежания дубликатов.
"""
import logging
import os
import shutil
import tempfile
import zipfile
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Entity, ImportLog, TaxPayment
from .tax_xml_parser import parse_tax_xml_file

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


async def _resolve_inns(
    db: AsyncSession,
    inns: set[str],
    cache: dict[str, int],
) -> dict[str, int]:
    unknown = [inn for inn in inns if inn not in cache]
    if not unknown:
        return cache
    result = await db.execute(
        select(Entity.id, Entity.inn).where(Entity.inn.in_(unknown))
    )
    for row in result:
        cache[row.inn] = row.id
    return cache


async def _flush_tax_batch(
    db: AsyncSession,
    batch: list[dict],
    id_by_inn: dict[str, int],
) -> int:
    if not batch:
        return 0

    rows = []
    for rec in batch:
        entity_id = id_by_inn.get(rec["inn"])
        if entity_id is None:
            continue
        rows.append(
            {
                "entity_id": entity_id,
                "doc_id": rec["doc_id"],
                "doc_date": rec["doc_date"],
                "data_date": rec["data_date"],
                "org_name": rec["org_name"],
                "tax_name": rec["tax_name"],
                "paid_amount": rec["paid_amount"],
            }
        )

    if not rows:
        return 0

    stmt = pg_insert(TaxPayment).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["entity_id", "doc_id", "tax_name"],
        set_={
            "doc_date": stmt.excluded.doc_date,
            "data_date": stmt.excluded.data_date,
            "org_name": stmt.excluded.org_name,
            "paid_amount": stmt.excluded.paid_amount,
        },
    )

    await db.execute(stmt)
    await db.commit()

    return len(rows)


async def import_tax_xml_file(
    filepath: str,
    filename: str,
    db: AsyncSession,
    import_log_id: Optional[int] = None,
) -> ImportLog:
    if import_log_id is not None:
        log = await db.get(ImportLog, import_log_id)
        if log is None:
            log = ImportLog(type="tax", filename=filename, status="processing")
            db.add(log)
            await db.commit()
            await db.refresh(log)
    else:
        log = ImportLog(type="tax", filename=filename, status="processing")
        db.add(log)
        await db.commit()
        await db.refresh(log)

    logger.info("Начало импорта налогов: '%s', import_id=%d", filename, log.id)

    total = 0
    total_inserted = 0
    id_by_inn: dict[str, int] = {}
    batch_no = 0

    try:
        batch: list[dict] = []

        for record in parse_tax_xml_file(filepath):
            batch.append(record)
            total += 1
            if len(batch) >= BATCH_SIZE:
                batch_no += 1
                logger.debug(
                    "Налоговый батч #%d: %d записей (всего: %d)", batch_no, len(batch), total,
                )
                id_by_inn = await _resolve_inns(
                    db, {r["inn"] for r in batch}, id_by_inn
                )
                ins = await _flush_tax_batch(db, batch, id_by_inn)
                total_inserted += ins
                batch.clear()

        if batch:
            batch_no += 1
            logger.debug("Финальный налоговый батч #%d: %d записей", batch_no, len(batch))
            id_by_inn = await _resolve_inns(
                db, {r["inn"] for r in batch}, id_by_inn
            )
            ins = await _flush_tax_batch(db, batch, id_by_inn)
            total_inserted += ins
            batch.clear()

        unlinked = total - total_inserted
        log.records_total = total
        log.records_inserted = total_inserted
        log.records_updated = 0
        log.status = "completed"
        if unlinked:
            log.error_message = (
                f"{unlinked} записей не привязано к организациям "
                f"(ИНН не найден в реестре МСП)"
            )
        await db.commit()
        await db.refresh(log)

        logger.info(
            "Импорт налогов завершён: '%s', всего=%d, вставлено=%d, не привязано=%d, батчей=%d",
            filename, total, total_inserted, unlinked, batch_no,
        )

    except Exception as e:
        logger.exception("Ошибка импорта налогового XML %s", filename)
        await db.rollback()
        log = await db.get(ImportLog, log.id)
        if log:
            log.status = "error"
            log.error_message = str(e)[:2000]
            log.records_total = total
            log.records_inserted = total_inserted
            await db.commit()
            await db.refresh(log)
        raise

    return log


async def _process_tax_file(
    filepath: str,
    db: AsyncSession,
    id_by_inn: dict[str, int],
) -> tuple[int, int]:
    """Обрабатывает один налоговый XML, возвращая (total, inserted)."""
    total = 0
    total_ins = 0
    batch: list[dict] = []

    for record in parse_tax_xml_file(filepath):
        batch.append(record)
        total += 1
        if len(batch) >= BATCH_SIZE:
            id_by_inn = await _resolve_inns(db, {r["inn"] for r in batch}, id_by_inn)
            total_ins += await _flush_tax_batch(db, batch, id_by_inn)
            batch.clear()

    if batch:
        id_by_inn = await _resolve_inns(db, {r["inn"] for r in batch}, id_by_inn)
        total_ins += await _flush_tax_batch(db, batch, id_by_inn)
        batch.clear()

    return total, total_ins


async def run_tax_import_task(filepath: str, filename: str, import_log_id: int):
    from ..database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            await import_tax_xml_file(
                filepath=filepath,
                filename=filename,
                db=session,
                import_log_id=import_log_id,
            )
        except Exception:
            logger.exception("run_tax_import_task: импорт завершился с ошибкой")


async def run_tax_import_zip_task(filepath: str, filename: str, import_log_id: int):
    from ..database import AsyncSessionLocal

    logger.info(
        "ZIP задача налогов: начало распаковки '%s' (import_id=%d)", filename, import_log_id,
    )

    extract_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(filepath) as zf:
            zf.extractall(extract_dir)
        logger.info("ZIP налогов распакован во временную директорию: %s", extract_dir)

        xml_files: list[str] = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith(".xml"):
                    xml_files.append(os.path.join(root, f))

        if not xml_files:
            raise ValueError("В ZIP архиве не найдено XML файлов")

        logger.info("В ZIP архиве налогов найдено XML файлов: %d", len(xml_files))

        async with AsyncSessionLocal() as session:
            log = await session.get(ImportLog, import_log_id)
            if log is None:
                log = ImportLog(type="tax", filename=filename, status="processing")
                session.add(log)
                await session.commit()
                await session.refresh(log)

            total = 0
            total_ins = 0
            id_by_inn: dict[str, int] = {}

            try:
                for idx, fpath in enumerate(xml_files, 1):
                    fname = os.path.basename(fpath)
                    logger.info(
                        "Обработка налогового файла [%d/%d]: '%s'", idx, len(xml_files), fname,
                    )
                    t, ins = await _process_tax_file(fpath, session, id_by_inn)
                    total += t
                    total_ins += ins
                    logger.info("Файл '%s' обработан: %d записей налогов", fname, t)

                log.records_total = total
                log.records_inserted = total_ins
                log.status = "completed"
                unlinked = total - total_ins
                if unlinked:
                    log.error_message = (
                        f"{unlinked} записей не привязано к организациям"
                    )
                await session.commit()

                logger.info(
                    "ZIP задача налогов завершена: '%s', всего=%d, вставлено=%d, не привязано=%d",
                    filename, total, total_ins, unlinked,
                )
            except Exception as e:
                logger.exception("run_tax_import_zip_task: ошибка импорта")
                await session.rollback()
                log = await session.get(ImportLog, import_log_id)
                if log:
                    log.status = "error"
                    log.error_message = str(e)[:2000]
                    log.records_total = total
                    log.records_inserted = total_ins
                    await session.commit()
    except zipfile.BadZipFile:
        logger.error("ZIP задача налогов: повреждённый архив '%s'", filename)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
        logger.debug("Временная директория налогов удалена: %s", extract_dir)
