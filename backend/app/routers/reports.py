import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..db_models import Report, Transaction

logger = logging.getLogger("cashflow_explainer")

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "created_at": r.created_at.isoformat(),
            "filename": r.filename,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "num_months": r.num_months,
            "net_cash_flow": r.net_cash_flow,
            "risk_score": r.risk_score,
            "risk_band": r.risk_band,
        }
        for r in reports
    ]


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return {
        "id": str(report.id),
        "created_at": report.created_at.isoformat(),
        "filename": report.filename,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "num_months": report.num_months,
        "net_cash_flow": report.net_cash_flow,
        "risk_score": report.risk_score,
        "risk_band": report.risk_band,
        "raw_data": report.raw_data,
    }


@router.delete("/{report_id}", status_code=204)
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    await db.delete(report)
    await db.commit()


@router.delete("", status_code=204)
async def clear_all_reports(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Transaction))
    await db.execute(delete(Report))
    await db.commit()
