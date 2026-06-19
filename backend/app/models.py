from datetime import datetime

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(3), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_composed: Mapped[Date | None] = mapped_column(Date, nullable=True)
    date_included: Mapped[Date | None] = mapped_column(Date, nullable=True)
    msp_type: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    msp_category: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_new: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    social_ent: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    employees_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    region_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    district_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    city_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    okved_main: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    okved_main_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    okved_ver: Mapped[str | None] = mapped_column(String(4), nullable=True)

    okved_list: Mapped[list["OkvedAdditional"]] = relationship(
        "OkvedAdditional",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="select",
    )
    licenses: Mapped[list["License"]] = relationship(
        "License",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="select",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="select",
    )
    partnerships: Mapped[list["Partnership"]] = relationship(
        "Partnership",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="select",
    )
    tax_payments: Mapped[list["TaxPayment"]] = relationship(
        "TaxPayment",
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="select",
    )


class OkvedAdditional(Base):
    __tablename__ = "okved_additional"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(4), nullable=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="okved_list")


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    series: Mapped[str | None] = mapped_column(String(10), nullable=True)
    number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lic_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    activity_names: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    date_issued: Mapped[Date | None] = mapped_column(Date, nullable=True)
    date_start: Mapped[Date | None] = mapped_column(Date, nullable=True)
    date_end: Mapped[Date | None] = mapped_column(Date, nullable=True)
    date_suspended: Mapped[Date | None] = mapped_column(Date, nullable=True)
    issued_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    suspended_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="licenses")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str | None] = mapped_column(String(18), nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_innovative: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="products")


class Partnership(Base):
    __tablename__ = "partnerships"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_inn: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    partner_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    contract_number: Mapped[str | None] = mapped_column(String(60), nullable=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="partnerships")


class ImportLog(Base):
    __tablename__ = "import_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(10), default="msp", nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    records_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processing", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class TaxPayment(Base):
    __tablename__ = "tax_payments"
    __table_args__ = (
        UniqueConstraint("entity_id", "doc_id", "tax_name", name="uq_tax_payment"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_id: Mapped[str] = mapped_column(String(36), nullable=False)
    doc_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    data_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    org_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    tax_name: Mapped[str] = mapped_column(Text, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="tax_payments")
