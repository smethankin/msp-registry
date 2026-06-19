"""
Потоковый парсер XML файлов ФНС с данными об уплаченных налогах.

Формат: https://file.nalog.ru/opendata/7707329152-paytax/structure-20180110.xsd
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Generator, Optional

from lxml import etree

logger = logging.getLogger(__name__)


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None
    value = value.strip().replace(" ", "")
    if not value:
        return None
    try:
        return Decimal(value)
    except (ValueError, TypeError):
        return None


def parse_tax_xml_file(filepath: str) -> Generator[dict, None, None]:
    """
    Потоковый генератор записей налогов из XML файла ФНС.

    Каждая запись — один налог (СвУплСумНал) с привязкой к организации (СведНП).
    """
    context = etree.iterparse(
        filepath,
        events=("end",),
        recover=True,
        huge_tree=True,
    )

    count = 0
    for event, elem in context:
        if _local(elem.tag) != "СвУплСумНал":
            continue

        parent = elem.getparent()
        while parent is not None and _local(parent.tag) != "Документ":
            parent = parent.getparent()

        if parent is None:
            elem.clear()
            continue

        doc_id = parent.get("ИдДок")
        doc_date = _parse_date(parent.get("ДатаДок"))
        data_date = _parse_date(parent.get("ДатаСост"))

        sved_np = None
        for child in parent:
            if _local(child.tag) == "СведНП":
                sved_np = child
                break

        inn = sved_np.get("ИННЮЛ") if sved_np is not None else None
        org_name = sved_np.get("НаимОрг") if sved_np is not None else None

        if not inn or not doc_id:
            elem.clear()
            continue

        count += 1
        record = {
            "inn": inn,
            "doc_id": doc_id,
            "doc_date": doc_date,
            "data_date": data_date,
            "org_name": org_name,
            "tax_name": elem.get("НаимНалог"),
            "paid_amount": _parse_decimal(elem.get("СумУплНал")),
        }

        yield record

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    logger.info("Парсер налогового XML: обработано %d записей из '%s'", count, filepath)
    del context
