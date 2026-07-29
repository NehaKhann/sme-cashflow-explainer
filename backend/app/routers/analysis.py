import asyncio
import io
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_optional_user
from ..database import get_db
from ..db_models import Report, Transaction, User
from ..models import InvalidTransactionData
from ..schemas import AnalysisResponse
from ..services.feature_extraction import extract_features, load_transactions
from ..services.narrative_generator import generate_narrative
from ..services.risk_scoring import assess_risk

logger = logging.getLogger("cashflow_explainer")

router = APIRouter(prefix="/api", tags=["analysis"])

MAX_FILE_SIZE_MB = 5


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_transactions(
    file: UploadFile = File(...),
    currency: str = Form("USD"),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

    try:
        df = load_transactions(io.BytesIO(raw))
        features = extract_features(df)
        risk = assess_risk(features)
        narrative = await asyncio.to_thread(generate_narrative, features, risk)
    except InvalidTransactionData as e:
        logger.warning("Invalid transaction data uploaded: %s", e)
        raise HTTPException(status_code=422, detail=str(e)) from None
    except Exception:
        logger.exception("Unexpected error during analysis")
        raise HTTPException(status_code=500, detail="Internal error while analyzing transactions.") from None

    now = datetime.now(UTC)
    report_id = uuid.uuid4()
    is_demo = current_user is None

    response = AnalysisResponse.build(features, risk, narrative, str(report_id), currency, is_demo)

    if current_user:
        report = Report(
            id=report_id,
            user_id=current_user.id,
            created_at=now,
            filename=file.filename,
            start_date=features.start_date,
            end_date=features.end_date,
            num_months=features.num_months,
            net_cash_flow=features.net_cash_flow,
            risk_score=risk.overall_score,
            risk_band=risk.overall_band,
            raw_data=response.model_dump(),
        )
        db.add(report)

        for _, row in df.iterrows():
            txn = Transaction(
                report_id=report_id,
                date=row["date"].to_pydatetime().date(),
                amount=float(row["amount"]),
                counterparty=str(row["counterparty"]),
                category=str(row.get("category", "uncategorized")),
            )
            db.add(txn)

        await db.commit()
    else:
        response = response.model_copy(update={"report_id": "demo"})

    return response
