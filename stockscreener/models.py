from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"
    company_id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    cik: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sector: Mapped[str] = mapped_column(String(100), default="Unknown")
    industry: Mapped[str] = mapped_column(String(120), default="Unknown")


class IndexMembership(Base):
    __tablename__ = "index_membership"
    membership_id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.company_id"), index=True)
    index_name: Mapped[str] = mapped_column(String(30), default="NDX")
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class PriceDaily(Base):
    __tablename__ = "prices_daily"
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.company_id"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    close: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    adjusted_close: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    volume: Mapped[int] = mapped_column(Integer)


class FinancialFactRaw(Base):
    __tablename__ = "financial_facts_raw"
    fact_id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.company_id"), index=True)
    taxonomy: Mapped[str] = mapped_column(String(30))
    concept: Mapped[str] = mapped_column(String(160))
    unit: Mapped[str] = mapped_column(String(30))
    value: Mapped[Decimal] = mapped_column(Numeric(24, 4))
    period_end: Mapped[date] = mapped_column(Date)
    filing_date: Mapped[date] = mapped_column(Date)
    form: Mapped[str] = mapped_column(String(20))
    accession_number: Mapped[str] = mapped_column(String(30), unique=True)


class Signal(Base):
    __tablename__ = "signals"
    signal_id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.company_id"), index=True)
    as_of: Mapped[date] = mapped_column(Date, index=True)
    dip_score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    quality_score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    valuation_score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    overall_score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    reason: Mapped[str] = mapped_column(Text)


class ScanLog(Base):
    __tablename__ = "scan_logs"
    scan_id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    period: Mapped[str] = mapped_column(String(10))
    universe_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


def database_session(database_url: str | None = None):
    engine = create_engine(database_url or "sqlite:///stockscreener.db")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()
