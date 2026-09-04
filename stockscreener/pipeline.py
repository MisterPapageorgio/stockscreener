from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError

from .models import Company, IndexMembership, PriceDaily, ScanLog, Signal, database_session
from .providers import enrich_company_profiles, live_prices, sec_fundamentals, universe
from .scoring import add_sector_trends, score_signals, technical_features


class ScanCancelled(Exception):
    pass


SCAN_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "scans"


def scan_cache_path(period: str) -> Path:
    return SCAN_CACHE_DIR / f"scan_{period}.pkl"


def load_cached_scan(period: str) -> pd.DataFrame | None:
    cache_path = scan_cache_path(period)
    if not cache_path.exists():
        return None
    try:
        return add_sector_trends(enrich_company_profiles(pd.read_pickle(cache_path)))
    except (OSError, ValueError, EOFError):
        return None


def save_cached_scan(result: pd.DataFrame, period: str) -> None:
    SCAN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    result.to_pickle(scan_cache_path(period))


def run_scan(live: bool = True, period: str = "5y", cancel_event: Event | None = None) -> pd.DataFrame:
    log_session = database_session(os.getenv("DATABASE_URL"))
    scan_log = ScanLog(started_at=datetime.now(timezone.utc), status="running", period=period)
    log_session.add(scan_log)
    log_session.commit()
    scan_id = scan_log.scan_id
    log_session.close()
    try:
        _check_cancel(cancel_event)
        companies = universe()
        _check_cancel(cancel_event)
        prices, benchmark = live_prices(companies.ticker.tolist(), period)
        _check_cancel(cancel_event)
        features = technical_features(prices, benchmark)
        _check_cancel(cancel_event)
        fundamentals = sec_fundamentals(companies, prices, cancel_event=cancel_event)
        _check_cancel(cancel_event)
        result = score_signals(features, fundamentals).merge(companies, on="ticker", how="left")
        result = add_sector_trends(result)
        _check_cancel(cancel_event)
        persist_snapshot(companies, prices, result)
        save_cached_scan(result, period)
        update_scan_log(scan_id, status="success", universe_count=len(companies), result_count=len(result))
        return result
    except ScanCancelled as exc:
        update_scan_log(scan_id, status="cancelled", error_message=str(exc))
        raise
    except Exception as exc:
        update_scan_log(scan_id, status="failed", error_message=str(exc))
        raise


def _check_cancel(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise ScanCancelled("Scan abgebrochen")


def update_scan_log(scan_id: int, **values: object) -> None:
    session = database_session(os.getenv("DATABASE_URL"))
    try:
        scan_log = session.get(ScanLog, scan_id)
        if scan_log is not None:
            for field, value in values.items():
                setattr(scan_log, field, value)
            scan_log.finished_at = datetime.now(timezone.utc)
            session.commit()
    finally:
        session.close()


def recent_scan_logs(limit: int = 25) -> pd.DataFrame:
    session = database_session(os.getenv("DATABASE_URL"))
    try:
        logs = session.query(ScanLog).order_by(ScanLog.started_at.desc()).limit(limit).all()
        return pd.DataFrame([
            {
                "Status": log.status,
                "Start": log.started_at,
                "Ende": log.finished_at,
                "Historie": log.period,
                "Universum": log.universe_count,
                "Ergebnisse": log.result_count,
                "Fehler": log.error_message or "",
            }
            for log in logs
        ])
    finally:
        session.close()


def persist_snapshot(companies: pd.DataFrame, prices: pd.DataFrame, signals: pd.DataFrame) -> None:
    session = database_session(os.getenv("DATABASE_URL"))
    try:
        company_ids = {}
        for row in companies.itertuples(index=False):
            company = session.query(Company).filter_by(ticker=row.ticker).one_or_none()
            if company is None:
                company = Company(ticker=row.ticker, company_name=row.company_name, sector=row.sector, industry=row.industry)
                try:
                    with session.begin_nested():
                        session.add(company)
                        session.flush()
                except IntegrityError:
                    company = session.query(Company).filter_by(ticker=row.ticker).one()
            else:
                company.company_name = row.company_name
                company.sector = row.sector
                company.industry = row.industry
            company.cik = str(row.cik) if pd.notna(row.cik) else None
            company_ids[row.ticker] = company.company_id
            if session.query(IndexMembership).filter_by(company_id=company.company_id, index_name="NDX").count() == 0:
                session.add(IndexMembership(company_id=company.company_id, index_name="NDX", valid_from=pd.Timestamp("2024-01-01").date()))

        snapshot_date = pd.Timestamp(signals["as_of"].max()).date()
        price_rows = [
            {
                "company_id": company_ids[row.ticker],
                "date": pd.Timestamp(row.date).date(),
                "close": row.adjusted_close,
                "adjusted_close": row.adjusted_close,
                "volume": int(row.volume),
            }
            for row in prices.itertuples(index=False)
        ]
        dialect = session.bind.dialect.name
        if dialect == "sqlite":
            price_insert = sqlite_insert(PriceDaily)
        elif dialect == "postgresql":
            price_insert = postgresql_insert(PriceDaily)
        else:
            price_insert = None
        if price_insert is not None:
            session.execute(
                price_insert.on_conflict_do_update(
                    index_elements=["company_id", "date"],
                    set_={
                        "close": price_insert.excluded.close,
                        "adjusted_close": price_insert.excluded.adjusted_close,
                        "volume": price_insert.excluded.volume,
                    },
                ),
                price_rows,
            )
        else:
            for row in price_rows:
                session.merge(PriceDaily(**row))

        session.execute(delete(Signal).where(Signal.as_of == snapshot_date))
        for row in signals.itertuples(index=False):
            session.add(Signal(company_id=company_ids[row.ticker], as_of=snapshot_date, dip_score=row.dip_score, quality_score=row.quality_score, valuation_score=row.valuation_score, overall_score=row.overall_score, reason=row.reason))
        session.commit()
    finally:
        session.close()
