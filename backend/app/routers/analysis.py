import io
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..services.feature_extraction import load_transactions, extract_features
from ..services.risk_scoring import assess_risk
from ..services.narrative_generator import generate_narrative
from ..models import InvalidTransactionData
from ..schemas import AnalysisResponse

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

    return AnalysisResponse.build(features, risk, narrative)
