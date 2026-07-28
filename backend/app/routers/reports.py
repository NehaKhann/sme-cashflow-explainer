import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..db_models import Report, Transaction, User
from ..auth import get_current_user
from ..schemas import TransactionResponse, CompareRequest, CompareResponse, AnalysisResponse

logger = logging.getLogger("cashflow_explainer")

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
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
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
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
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    await db.delete(report)
    await db.commit()


@router.delete("", status_code=204)
async def clear_all_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        delete(Transaction).where(
            Transaction.report_id.in_(
                select(Report.id).where(Report.user_id == current_user.id)
            )
        )
    )
    await db.execute(
        delete(Report).where(Report.user_id == current_user.id)
    )
    await db.commit()


@router.get("/{report_id}/transactions")
async def get_transactions(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    txn_result = await db.execute(
        select(Transaction)
        .where(Transaction.report_id == report_id)
        .order_by(Transaction.date.desc())
    )
    transactions = txn_result.scalars().all()
    return [
        TransactionResponse(
            id=str(t.id),
            date=t.date.isoformat(),
            amount=t.amount,
            counterparty=t.counterparty,
            category=t.category,
        )
        for t in transactions
    ]


@router.post("/compare")
async def compare_reports(
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(body.report_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly two report IDs are required.")

    reports = []
    for rid in body.report_ids:
        result = await db.execute(
            select(Report).where(Report.id == rid, Report.user_id == current_user.id)
        )
        r = result.scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail=f"Report {rid} not found.")
        reports.append(r)

    ra, rb = reports
    data_a = AnalysisResponse(**ra.raw_data)
    data_b = AnalysisResponse(**rb.raw_data)

    deltas = {
        "net_cash_flow": round(data_b.net_cash_flow - data_a.net_cash_flow, 2),
        "revenue_volatility_pct": round(data_b.revenue_volatility_pct - data_a.revenue_volatility_pct, 2),
        "top_customer_share_pct": round(data_b.top_customer_share_pct - data_a.top_customer_share_pct, 2),
        "risk_score": data_b.risk_score - data_a.risk_score,
        "avg_monthly_burn": round(data_b.avg_monthly_burn - data_a.avg_monthly_burn, 2),
        "total_inflow": round(data_b.total_inflow - data_a.total_inflow, 2),
        "total_outflow": round(data_b.total_outflow - data_a.total_outflow, 2),
    }

    return CompareResponse(report_a=data_a, report_b=data_b, deltas=deltas)
