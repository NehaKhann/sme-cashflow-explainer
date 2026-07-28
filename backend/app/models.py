from dataclasses import dataclass, field
from typing import Optional


class InvalidTransactionData(ValueError):
    """Raised when the uploaded CSV doesn't match the expected schema."""


@dataclass
class CashFlowFeatures:
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
    seasonal_low_months: list = field(default_factory=list)
    seasonal_high_months: list = field(default_factory=list)

    monthly_expenses: dict = field(default_factory=dict)
    expense_by_category: dict = field(default_factory=dict)
    avg_monthly_burn: float = 0.0

    months_of_negative_flow: int = 0
    longest_negative_streak_months: int = 0


@dataclass
class RiskFlag:
    severity: str
    code: str
    message: str


@dataclass
class RiskAssessment:
    overall_score: int
    overall_band: str
    flags: list[RiskFlag]
