"""
Импортер XML/ZIP файлов ФНС в базу данных.

Использует батч-апсерт по INN с пересозданием связанных записей.
"""
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Entity, ImportLog, License, OkvedAdditional, Partnership, Product
from .xml_parser import parse_xml_file

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


ENTITY_COLUMNS = [
    "doc_id",
    "entity_type",
    "inn",
    "ogrn",
    "full_name",
    "short_name",
    "date_composed",
    "date_included",
    "msp_type",
    "msp_category",
    "is_new",
    "social_ent",
    "employees_count",
    "region_code",
    "region_name",
    "district_name",
    "city_name",
    "locality_name",
    "okved_main",
    "okved_main_name",
    "okved_ver",
]


async def _flush_batch(
    db: AsyncSession,
    batch: list[dict],
) -> tuple[int, int]:
    """
    Apсёртит батч записей в entities и пересоздаёт связанные данные.
    Возвращает (inserted_count, updated_count).
    """
    if not batch:
        return 0, 0

    # Дедупликация внутри батча по inn — последняя запись побеждает
    by_inn: dict[str, dict] = {}
    for rec in batch:
        by_inn[rec["inn"]] = rec
    deduped = list(by_inn.values())

    # 1. Перед апсёртом узнаем, какие INN уже существуют
    inns = [r["inn"] for r in deduped]
    existing_rows = await db.execute(
        select(Entity.id, Entity.inn).where(Entity.inn.in_(inns))
    )
    existing_map = {row.inn: row.id for row in existing_rows}
    updated_count = len(existing_map)
    inserted_count = len(deduped) - updated_count

    # 2. Upsert в entities
    entity_payload = [{col: rec.get(col) for col in ENTITY_COLUMNS} for rec in deduped]
    stmt = pg_insert(Entity).values(entity_payload)
    update_cols = {col: stmt.excluded[col] for col in ENTITY_COLUMNS if col != "inn"}
    stmt = stmt.on_conflict_do_update(
        index_elements=["inn"],
        set_=update_cols,
    ).returning(Entity.id, Entity.inn)

    result = await db.execute(stmt)
    id_by_inn: dict[str, int] = {row.inn: row.id for row in result}

    # 3. Удалить старые связанные записи для всех затронутых entity_id
    all_entity_ids = list(id_by_inn.values())
    if all_entity_ids:
        for model in (OkvedAdditional, License, Product, Partnership):
            await db.execute(
                delete(model).where(model.entity_id.in_(all_entity_ids))
            )

    # 4. Bulk insert связанных данных
    okved_rows: list[dict] = []
    license_rows: list[dict] = []
    product_rows: list[dict] = []
    partnership_rows: list[dict] = []

    for rec in deduped:
        entity_id = id_by_inn.get(rec["inn"])
        if entity_id is None:
            continue

        for ok in rec.get("okved_additional") or []:
            okved_rows.append({"entity_id": entity_id, **ok})

        for lic in rec.get("licenses") or []:
            license_rows.append({"entity_id": entity_id, **lic})

        for prod in rec.get("products") or []:
            product_rows.append({"entity_id": entity_id, **prod})

        for pp in rec.get("partnerships") or []:
            partnership_rows.append({"entity_id": entity_id, **pp})

    if okved_rows:
        await db.execute(pg_insert(OkvedAdditional).values(okved_rows))
    if license_rows:
        await db.execute(pg_insert(License).values(license_rows))
    if product_rows:
        await db.execute(pg_insert(Product).values(product_rows))
    if partnership_rows:
        await db.execute(pg_insert(Partnership).values(partnership_rows))

    await db.commit()

    return inserted_count, updated_count


async def import_xml_file(
    filepath: str,
    filename: str,
    db: AsyncSession,
    import_log_id: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> ImportLog:
    if import_log_id is not None:
        log = await db.get(ImportLog, import_log_id)
        if log is None:
            log = ImportLog(filename=filename, status="processing")
            db.add(log)
            await db.commit()
            await db.refresh(log)
    else:
        log = ImportLog(filename=filename, status="processing")
        db.add(log)
        await db.commit()
        await db.refresh(log)

    logger.info("Начало импорта MSP: '%s', import_id=%d", filename, log.id)

    total = 0
    total_inserted = 0
    total_updated = 0
    batch_no = 0

    try:
        batch: list[dict] = []

        for record in parse_xml_file(filepath):
            batch.append(record)
            total += 1

            if len(batch) >= BATCH_SIZE:
                batch_no += 1
                logger.debug(
                    "Батч #%d: %d записей (всего обработано: %d)", batch_no, len(batch), total,
                )
                ins, upd = await _flush_batch(db, batch)
                total_inserted += ins
                total_updated += upd
                batch.clear()

                if progress_callback:
                    progress_callback(total, total)

        if batch:
            batch_no += 1
            logger.debug("Финальный батч #%d: %d записей", batch_no, len(batch))
            ins, upd = await _flush_batch(db, batch)
            total_inserted += ins
            total_updated += upd
            batch.clear()

        log.records_total = total
        log.records_inserted = total_inserted
        log.records_updated = total_updated
        log.status = "completed"
        await db.commit()
        await db.refresh(log)

        logger.info(
            "Импорт MSP завершён: '%s', всего=%d, вставлено=%d, обновлено=%d, батчей=%d",
            filename, total, total_inserted, total_updated, batch_no,
        )

    except Exception as e:
        logger.exception("Ошибка импорта XML файла %s", filename)
        await db.rollback()
        log = await db.get(ImportLog, log.id)
        if log:
            log.status = "error"
            log.error_message = str(e)[:2000]
            log.records_total = total
            log.records_inserted = total_inserted
            log.records_updated = total_updated
            await db.commit()
            await db.refresh(log)
        raise

    return log


async def import_multiple_xml_files(
    file_specs: list[tuple[str, str]],
    db: AsyncSession,
    import_log_id: int,
) -> ImportLog:
    log = await db.get(ImportLog, import_log_id)
    if log is None:
        raise ValueError(f"ImportLog с id {import_log_id} не найден")

    logger.info(
        "Начало импорта нескольких MSP XML файлов: %d файлов, import_id=%d",
        len(file_specs), import_log_id,
    )

    total = 0
    total_inserted = 0
    total_updated = 0

    try:
        for idx, (filepath, filename) in enumerate(file_specs, 1):
            logger.info("Обработка файла [%d/%d]: '%s'", idx, len(file_specs), filename)
            batch: list[dict] = []
            file_count = 0
            for record in parse_xml_file(filepath):
                batch.append(record)
                total += 1
                file_count += 1
                if len(batch) >= BATCH_SIZE:
                    ins, upd = await _flush_batch(db, batch)
                    total_inserted += ins
                    total_updated += upd
                    batch.clear()
            if batch:
                ins, upd = await _flush_batch(db, batch)
                total_inserted += ins
                total_updated += upd
                batch.clear()
            logger.info("Файл '%s' обработан: %d записей", filename, file_count)

        log.records_total = total
        log.records_inserted = total_inserted
        log.records_updated = total_updated
        log.status = "completed"
        await db.commit()
        await db.refresh(log)

        logger.info(
            "Импорт нескольких MSP файлов завершён: всего=%d, вставлено=%d, обновлено=%d",
            total, total_inserted, total_updated,
        )

    except Exception as e:
        logger.exception("Ошибка импорта множественных XML файлов")
        await db.rollback()
        log = await db.get(ImportLog, log.id)
        if log:
            log.status = "error"
            log.error_message = str(e)[:2000]
            log.records_total = total
            log.records_inserted = total_inserted
            log.records_updated = total_updated
            await db.commit()
            await db.refresh(log)
        raise

    return log


async def run_import_task(filepath: str, filename: str, import_log_id: int):
    """
    Задача для BackgroundTasks: создаёт новую сессию БД и запускает импорт.
    """
    from ..database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            await import_xml_file(
                filepath=filepath,
                filename=filename,
                db=session,
                import_log_id=import_log_id,
            )
        except Exception:
            logger.exception("run_import_task: импорт завершился с ошибкой")


async def run_import_zip_task(filepath: str, filename: str, import_log_id: int):
    from ..database import AsyncSessionLocal

    logger.info("ZIP задача MSP: начало распаковки '%s' (import_id=%d)", filename, import_log_id)

    extract_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(filepath) as zf:
            zf.extractall(extract_dir)
        logger.info("ZIP распакован во временную директорию: %s", extract_dir)

        xml_files: list[tuple[str, str]] = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith(".xml"):
                    xml_files.append((os.path.join(root, f), f))

        if not xml_files:
            raise ValueError("В ZIP архиве не найдено XML файлов")

        logger.info(
            "В ZIP архиве найдено XML файлов: %d", len(xml_files),
        )

        async with AsyncSessionLocal() as session:
            try:
                await import_multiple_xml_files(
                    file_specs=xml_files,
                    db=session,
                    import_log_id=import_log_id,
                )
                logger.info("ZIP задача MSP завершена: '%s'", filename)
            except Exception:
                logger.exception("run_import_zip_task: импорт завершился с ошибкой")
    except zipfile.BadZipFile:
        logger.error("ZIP задача: повреждённый архив '%s'", filename)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)
        logger.debug("Временная директория удалена: %s", extract_dir)
