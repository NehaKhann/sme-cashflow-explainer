from pydantic import BaseModel
from typing import Optional
from .models import CashFlowFeatures, RiskFlag, RiskAssessment


class RiskFlagResponse(BaseModel):
    severity: str
    code: str
    message: str


class AnalysisResponse(BaseModel):
    report_id: str
    start_date: str
    end_date: str
    num_months: int

    total_inflow: float
    total_outflow: float
    net_cash_flow: float

    monthly_revenue: dict
    revenue_volatility_pct: float
    largest_mom_drop_pct: float
    largest_mom_drop_month: Optional[str]

    top_customer_share_pct: float
    top_customer_name: Optional[str]
    top_3_customer_share_pct: float
    num_unique_customers: int

    seasonality_detected: bool
    seasonal_low_months: list
    seasonal_high_months: list

    monthly_expenses: dict
    expense_by_category: dict
    avg_monthly_burn: float
    months_of_negative_flow: int
    longest_negative_streak_months: int

    risk_score: int
    risk_band: str
    risk_flags: list[RiskFlagResponse]

    narrative: str
    currency: str = "USD"
    demo: bool = False

    @classmethod
    def build(cls, features: CashFlowFeatures, risk: RiskAssessment, narrative: str, report_id: str, currency: str = "USD", demo: bool = False) -> "AnalysisResponse":
        data = {k: getattr(features, k) for k in features.__dataclass_fields__}
        data["risk_score"] = risk.overall_score
        data["risk_band"] = risk.overall_band
        data["risk_flags"] = [RiskFlagResponse(severity=f.severity, code=f.code, message=f.message) for f in risk.flags]
        data["narrative"] = narrative
        data["report_id"] = report_id
        data["currency"] = currency
        data["demo"] = demo
        return cls(**data)


class TransactionResponse(BaseModel):
    id: str
    date: str
    amount: float
    counterparty: str
    category: str


class CompareRequest(BaseModel):
    report_ids: list[str]


class CompareResponse(BaseModel):
    report_a: AnalysisResponse
    report_b: AnalysisResponse
    deltas: dict


class ErrorResponse(BaseModel):
    detail: str
