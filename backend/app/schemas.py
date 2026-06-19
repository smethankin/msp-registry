from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


# ОКВЭД
class OkvedAdditionalOut(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    model_config = {"from_attributes": True}


# Лицензия
class LicenseOut(BaseModel):
    series: Optional[str] = None
    number: Optional[str] = None
    lic_type: Optional[str] = None
    activity_names: Optional[List[str]] = None
    date_issued: Optional[date] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    date_suspended: Optional[date] = None
    issued_by: Optional[str] = None
    suspended_by: Optional[str] = None
    model_config = {"from_attributes": True}


# Продукция
class ProductOut(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    is_innovative: Optional[bool] = None
    model_config = {"from_attributes": True}


# Партнёрство
class PartnershipOut(BaseModel):
    partner_inn: Optional[str] = None
    partner_name: Optional[str] = None
    contract_date: Optional[date] = None
    contract_number: Optional[str] = None
    model_config = {"from_attributes": True}


# Полные данные сущности
class EntityDetail(BaseModel):
    id: int
    doc_id: str
    entity_type: str
    inn: str
    ogrn: Optional[str] = None
    full_name: Optional[str] = None
    short_name: Optional[str] = None
    date_composed: Optional[date] = None
    date_included: Optional[date] = None
    msp_type: Optional[int] = None
    msp_category: Optional[int] = None
    is_new: Optional[int] = None
    social_ent: Optional[int] = None
    employees_count: Optional[int] = None
    region_code: Optional[str] = None
    region_name: Optional[str] = None
    district_name: Optional[str] = None
    city_name: Optional[str] = None
    locality_name: Optional[str] = None
    okved_main: Optional[str] = None
    okved_main_name: Optional[str] = None
    okved_ver: Optional[str] = None
    okved_list: List[OkvedAdditionalOut] = []
    licenses: List[LicenseOut] = []
    products: List[ProductOut] = []
    partnerships: List[PartnershipOut] = []
    model_config = {"from_attributes": True}


# Краткая карточка для поиска
class EntityCard(BaseModel):
    inn: str
    entity_type: str
    full_name: Optional[str] = None
    ogrn: Optional[str] = None
    region_name: Optional[str] = None
    okved_main: Optional[str] = None
    okved_main_name: Optional[str] = None
    msp_category: Optional[int] = None
    date_included: Optional[date] = None
    model_config = {"from_attributes": True}


# Результаты поиска
class SearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[EntityCard]


# Журнал загрузок
# Уплаченные налоги
class TaxPaymentOut(BaseModel):
    doc_id: str
    doc_date: Optional[date] = None
    data_date: Optional[date] = None
    org_name: Optional[str] = None
    tax_name: str
    paid_amount: float
    model_config = {"from_attributes": True}


# Журнал загрузок
class ImportLogOut(BaseModel):
    id: int
    type: str = "msp"
    filename: str
    uploaded_at: datetime
    records_total: int
    records_inserted: int
    records_updated: int
    status: str
    error_message: Optional[str] = None
    model_config = {"from_attributes": True}


# Статистика
class StatsOut(BaseModel):
    total_entities: int
    total_ip: int
    total_org: int
    total_tax_records: int = 0
    last_import: Optional[datetime] = None
