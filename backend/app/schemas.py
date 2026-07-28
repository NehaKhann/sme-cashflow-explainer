from pydantic import BaseModel
from typing import Optional


class RiskFlagResponse(BaseModel):
    severity: str
    code: str
    message: str


class AnalysisResponse(BaseModel):
    # period
    start_date: str
    end_date: str
    num_months: int

    # top-line
    total_inflow: float
    total_outflow: float
    net_cash_flow: float

    # volatility
    monthly_revenue: dict
    revenue_volatility_pct: float
    largest_mom_drop_pct: float
    largest_mom_drop_month: Optional[str]

    # concentration
    top_customer_share_pct: float
    top_customer_name: Optional[str]
    top_3_customer_share_pct: float
    num_unique_customers: int

    # seasonality
    seasonality_detected: bool
    seasonal_low_months: list
    seasonal_high_months: list

    # expenses
    monthly_expenses: dict
    expense_by_category: dict
    avg_monthly_burn: float
    months_of_negative_flow: int
    longest_negative_streak_months: int

    # risk
    risk_score: int
    risk_band: str
    risk_flags: list[RiskFlagResponse]

    # narrative
    narrative: str


class ErrorResponse(BaseModel):
    detail: str
