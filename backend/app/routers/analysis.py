import io
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..services.feature_extraction import load_transactions, extract_features, InvalidTransactionData
from ..services.risk_scoring import assess_risk
from ..services.narrative_generator import generate_narrative
from ..schemas import AnalysisResponse, RiskFlagResponse

logger = logging.getLogger("cashflow_explainer")

router = APIRouter(prefix="/api", tags=["analysis"])

MAX_FILE_SIZE_MB = 5


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_transactions(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

    try:
        df = load_transactions(io.BytesIO(raw))
        features = extract_features(df)
        risk = assess_risk(features)
        narrative = generate_narrative(features, risk)
    except InvalidTransactionData as e:
        logger.warning("Invalid transaction data uploaded: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during analysis")
        raise HTTPException(status_code=500, detail="Internal error while analyzing transactions.")

    return AnalysisResponse(
        start_date=features.start_date,
        end_date=features.end_date,
        num_months=features.num_months,
        total_inflow=features.total_inflow,
        total_outflow=features.total_outflow,
        net_cash_flow=features.net_cash_flow,
        monthly_revenue=features.monthly_revenue,
        revenue_volatility_pct=features.revenue_volatility_pct,
        largest_mom_drop_pct=features.largest_mom_drop_pct,
        largest_mom_drop_month=features.largest_mom_drop_month,
        top_customer_share_pct=features.top_customer_share_pct,
        top_customer_name=features.top_customer_name,
        top_3_customer_share_pct=features.top_3_customer_share_pct,
        num_unique_customers=features.num_unique_customers,
        seasonality_detected=features.seasonality_detected,
        seasonal_low_months=features.seasonal_low_months,
        seasonal_high_months=features.seasonal_high_months,
        monthly_expenses=features.monthly_expenses,
        expense_by_category=features.expense_by_category,
        avg_monthly_burn=features.avg_monthly_burn,
        months_of_negative_flow=features.months_of_negative_flow,
        longest_negative_streak_months=features.longest_negative_streak_months,
        risk_score=risk.overall_score,
        risk_band=risk.overall_band,
        risk_flags=[RiskFlagResponse(severity=f.severity, code=f.code, message=f.message) for f in risk.flags],
        narrative=narrative,
    )
