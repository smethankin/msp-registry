"""
Потоковый парсер XML файлов Реестра МСП ФНС России.

Использует lxml.etree.iterparse для обработки очень больших XML файлов
с минимальным потреблением памяти.

Поддерживает оба варианта XML: с namespace и без.
"""
import logging
from datetime import date, datetime
from typing import Generator, Optional

from lxml import etree

logger = logging.getLogger(__name__)


def _local(tag: str) -> str:
    """Убирает namespace prefix из тега, если он есть."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Конвертирует строку 'ДД.ММ.ГГГГ' в date."""
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


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _find_child(elem, name: str):
    """Находит прямого потомка по локальному имени (игнорируя namespace)."""
    for child in elem:
        if _local(child.tag) == name:
            return child
    return None


def _find_children(elem, name: str):
    """Находит всех прямых потомков по локальному имени."""
    return [child for child in elem if _local(child.tag) == name]


def _parse_address(sved_mn) -> dict:
    """Парсит блок СведМН с адресом."""
    result = {
        "region_code": sved_mn.get("КодРегион"),
        "region_name": None,
        "district_name": None,
        "city_name": None,
        "locality_name": None,
    }
    for child in sved_mn:
        local = _local(child.tag)
        tip = child.get("Тип") or ""
        naim = child.get("Наим") or ""
        full = f"{tip} {naim}".strip() if tip else naim
        if local == "Регион":
            result["region_name"] = full or None
        elif local == "Район":
            result["district_name"] = full or None
        elif local == "Город":
            result["city_name"] = full or None
        elif local == "НаселПункт":
            result["locality_name"] = full or None
    return result


def _parse_okved(sv_okved) -> dict:
    """Парсит блок СвОКВЭД."""
    result = {
        "okved_main": None,
        "okved_main_name": None,
        "okved_ver": None,
        "okved_additional": [],
    }
    osn = _find_child(sv_okved, "СвОКВЭДОсн")
    if osn is not None:
        result["okved_main"] = osn.get("КодОКВЭД")
        result["okved_main_name"] = osn.get("НаимОКВЭД")
        result["okved_ver"] = osn.get("ВерсОКВЭД")
    for dop in _find_children(sv_okved, "СвОКВЭДДоп"):
        result["okved_additional"].append(
            {
                "code": dop.get("КодОКВЭД"),
                "name": dop.get("НаимОКВЭД"),
                "version": dop.get("ВерсОКВЭД"),
            }
        )
    return result


def _parse_license(sv_lic) -> dict:
    activity_names = []
    for vd in _find_children(sv_lic, "НаимЛицВД"):
        # НаимЛицВД может быть атрибутом или текстом
        name = vd.get("НаимЛицВД") or (vd.text or "").strip()
        if name:
            activity_names.append(name)
    return {
        "series": sv_lic.get("СерЛиценз"),
        "number": sv_lic.get("НомЛиценз"),
        "lic_type": sv_lic.get("ВидЛиценз"),
        "activity_names": activity_names or None,
        "date_issued": _parse_date(sv_lic.get("ДатаЛиценз")),
        "date_start": _parse_date(sv_lic.get("ДатаНачЛиценз")),
        "date_end": _parse_date(sv_lic.get("ДатаКонЛиценз")),
        "date_suspended": _parse_date(sv_lic.get("ДатаОстЛиценз")),
        "issued_by": sv_lic.get("ОргВыдЛиценз"),
        "suspended_by": sv_lic.get("ОргОстЛиценз"),
    }


def _parse_product(sv_prod) -> dict:
    pr = sv_prod.get("ПрОтнПрод")
    return {
        "code": sv_prod.get("КодПрод"),
        "name": sv_prod.get("НаимПрод"),
        "is_innovative": pr == "1" if pr is not None else None,
    }


def _parse_partnership(sv_pp) -> dict:
    return {
        "partner_inn": sv_pp.get("ИННЮЛ_ПП"),
        "partner_name": sv_pp.get("НаимЮЛ_ПП"),
        "contract_date": _parse_date(sv_pp.get("ДатаДог")),
        "contract_number": sv_pp.get("НомДог"),
    }


def _parse_document(doc) -> Optional[dict]:
    """Парсит один <Документ>. Возвращает None, если запись невалидна."""
    record = {
        "doc_id": doc.get("ИдДок"),
        "entity_type": None,
        "inn": None,
        "ogrn": None,
        "full_name": None,
        "short_name": None,
        "date_composed": _parse_date(doc.get("ДатаСост")),
        "date_included": _parse_date(doc.get("ДатаВклМСП")),
        "msp_type": _parse_int(doc.get("ВидСубМСП")),
        "msp_category": _parse_int(doc.get("КатСубМСП")),
        "is_new": _parse_int(doc.get("ПризНовМСП")),
        "social_ent": _parse_int(doc.get("СведСоцПред")),
        "employees_count": _parse_int(doc.get("ССЧР")),
        "region_code": None,
        "region_name": None,
        "district_name": None,
        "city_name": None,
        "locality_name": None,
        "okved_main": None,
        "okved_main_name": None,
        "okved_ver": None,
        "okved_additional": [],
        "licenses": [],
        "products": [],
        "partnerships": [],
    }

    # Юр.лицо или ИП
    org = _find_child(doc, "ОргВклМСП")
    ip = _find_child(doc, "ИПВклМСП")

    if org is not None:
        record["entity_type"] = "ORG"
        record["full_name"] = org.get("НаимОрг")
        record["short_name"] = org.get("НаимОргСокр")
        record["inn"] = org.get("ИННЮЛ")
        record["ogrn"] = org.get("ОГРН")
    elif ip is not None:
        record["entity_type"] = "IP"
        record["inn"] = ip.get("ИННФЛ")
        record["ogrn"] = ip.get("ОГРНИП")
        fio = _find_child(ip, "ФИОИП")
        if fio is not None:
            parts = [
                fio.get("Фамилия") or "",
                fio.get("Имя") or "",
                fio.get("Отчество") or "",
            ]
            full = " ".join(p for p in parts if p).strip()
            record["full_name"] = full or None
    else:
        return None

    if not record["inn"] or not record["doc_id"]:
        return None

    # Адрес
    sved_mn = _find_child(doc, "СведМН")
    if sved_mn is not None:
        record.update(_parse_address(sved_mn))

    # ОКВЭД
    sv_okved = _find_child(doc, "СвОКВЭД")
    if sv_okved is not None:
        record.update(_parse_okved(sv_okved))

    # Лицензии
    for sv_lic in _find_children(doc, "СвЛиценз"):
        record["licenses"].append(_parse_license(sv_lic))

    # Продукция
    for sv_prod in _find_children(doc, "СвПрод"):
        record["products"].append(_parse_product(sv_prod))

    # Партнёрство
    for sv_pp in _find_children(doc, "СвПрогПарт"):
        record["partnerships"].append(_parse_partnership(sv_pp))

    return record


def parse_xml_file(filepath: str) -> Generator[dict, None, None]:
    """
    Потоковый генератор записей из XML файла ФНС МСП.

    Использует iterparse с end-events и очисткой памяти после каждого
    обработанного <Документ>.
    """
    context = etree.iterparse(
        filepath,
        events=("end",),
        recover=True,
        huge_tree=True,
    )

    count = 0
    for event, elem in context:
        if _local(elem.tag) != "Документ":
            continue
        try:
            record = _parse_document(elem)
            if record:
                count += 1
                yield record
        finally:
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

    logger.info("Парсер MSP XML: обработано %d записей из '%s'", count, filepath)
    del context
