"""
Feature extraction engine for SME cash-flow analysis.

Design principle: this module computes every number that will ever appear
in a narrative. The LLM layer (narrative_generator.py) is only allowed to
explain these pre-computed numbers in prose -- it never calculates anything
itself. This keeps the system auditable: any claim in the final report can
be traced back to a specific pandas computation here.

Expected input schema (a CSV with these columns, case-insensitive):
    date        - transaction date (parseable by pandas)
    amount      - signed amount; positive = inflow, negative = outflow
    counterparty - name of the payer/payee (used for concentration risk)
    category    - optional; e.g. "revenue", "payroll", "rent", "supplies"
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


REQUIRED_COLUMNS = {"date", "amount", "counterparty"}


class InvalidTransactionData(ValueError):
    """Raised when the uploaded CSV doesn't match the expected schema."""


@dataclass
class CashFlowFeatures:
    # -- period covered --
    start_date: str
    end_date: str
    num_months: int

    # -- top-line --
    total_inflow: float
    total_outflow: float
    net_cash_flow: float

    # -- volatility --
    monthly_revenue: dict  # {"2026-01": 12000.0, ...}
    revenue_volatility_pct: float  # coefficient of variation, as %
    largest_mom_drop_pct: float  # biggest single month-over-month revenue drop
    largest_mom_drop_month: Optional[str]

    # -- concentration risk --
    top_customer_share_pct: float
    top_customer_name: Optional[str]
    top_3_customer_share_pct: float
    num_unique_customers: int

    # -- seasonality --
    seasonality_detected: bool
    seasonal_low_months: list = field(default_factory=list)
    seasonal_high_months: list = field(default_factory=list)

    # -- expense structure --
    monthly_expenses: dict = field(default_factory=dict)
    expense_by_category: dict = field(default_factory=dict)
    avg_monthly_burn: float = 0.0

    # -- runway --
    months_of_negative_flow: int = 0
    longest_negative_streak_months: int = 0


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def _validate(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise InvalidTransactionData(
            f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
            f"Required columns: {', '.join(sorted(REQUIRED_COLUMNS))}"
        )
    if df.empty:
        raise InvalidTransactionData("CSV contains no transaction rows.")


def load_transactions(csv_path_or_buffer) -> pd.DataFrame:
    """Load and validate a transaction CSV. Raises InvalidTransactionData on bad input."""
    df = pd.read_csv(csv_path_or_buffer)
    df = _normalize_columns(df)
    _validate(df)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        bad_rows = df[df["date"].isna()].index.tolist()
        raise InvalidTransactionData(
            f"Could not parse 'date' for row(s): {bad_rows[:5]}"
            + (" (and more)" if len(bad_rows) > 5 else "")
        )

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if df["amount"].isna().any():
        raise InvalidTransactionData("Column 'amount' contains non-numeric values.")

    if "category" not in df.columns:
        df["category"] = "uncategorized"
    df["category"] = df["category"].fillna("uncategorized")
    df["counterparty"] = df["counterparty"].fillna("unknown")

    df = df.sort_values("date").reset_index(drop=True)
    return df


def extract_features(df: pd.DataFrame) -> CashFlowFeatures:
    """Compute every cash-flow risk metric the narrative layer is allowed to reference."""
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)

    inflows = df[df["amount"] > 0]
    outflows = df[df["amount"] < 0]

    total_inflow = float(inflows["amount"].sum())
    total_outflow = float(outflows["amount"].sum())  # negative number
    net_cash_flow = float(df["amount"].sum())

    # ---- monthly revenue series ----
    monthly_rev_series = inflows.groupby("month")["amount"].sum().sort_index()
    monthly_revenue = {k: round(float(v), 2) for k, v in monthly_rev_series.items()}

    if len(monthly_rev_series) >= 2 and monthly_rev_series.mean() != 0:
        revenue_volatility_pct = round(
            float(monthly_rev_series.std() / monthly_rev_series.mean() * 100), 1
        )
    else:
        revenue_volatility_pct = 0.0

    mom_pct_change = monthly_rev_series.pct_change() * 100
    if not mom_pct_change.dropna().empty:
        largest_drop_idx = mom_pct_change.idxmin()
        largest_mom_drop_pct = round(float(mom_pct_change.min()), 1)
        largest_mom_drop_month = str(largest_drop_idx)
    else:
        largest_mom_drop_pct = 0.0
        largest_mom_drop_month = None

    # ---- customer concentration (based on inflows only) ----
    by_customer = inflows.groupby("counterparty")["amount"].sum().sort_values(ascending=False)
    num_unique_customers = int(by_customer.shape[0])
    if total_inflow > 0 and not by_customer.empty:
        top_customer_name = str(by_customer.index[0])
        top_customer_share_pct = round(float(by_customer.iloc[0] / total_inflow * 100), 1)
        top_3_share = float(by_customer.iloc[:3].sum() / total_inflow * 100)
        top_3_customer_share_pct = round(top_3_share, 1)
    else:
        top_customer_name = None
        top_customer_share_pct = 0.0
        top_3_customer_share_pct = 0.0

    # ---- seasonality (simple heuristic: months >20% below/above the mean) ----
    seasonal_low_months, seasonal_high_months = [], []
    seasonality_detected = False
    if len(monthly_rev_series) >= 4:
        mean_rev = monthly_rev_series.mean()
        low_threshold = mean_rev * 0.8
        high_threshold = mean_rev * 1.2
        seasonal_low_months = monthly_rev_series[monthly_rev_series < low_threshold].index.tolist()
        seasonal_high_months = monthly_rev_series[monthly_rev_series > high_threshold].index.tolist()
        seasonality_detected = bool(seasonal_low_months or seasonal_high_months)

    # ---- expenses ----
    monthly_exp_series = outflows.groupby("month")["amount"].sum().abs().sort_index()
    monthly_expenses = {k: round(float(v), 2) for k, v in monthly_exp_series.items()}
    avg_monthly_burn = round(float(monthly_exp_series.mean()), 2) if not monthly_exp_series.empty else 0.0

    expense_by_category = (
        outflows.groupby("category")["amount"].sum().abs().sort_values(ascending=False)
    )
    expense_by_category = {k: round(float(v), 2) for k, v in expense_by_category.items()}

    # ---- negative flow streaks ----
    monthly_net = df.groupby("month")["amount"].sum().sort_index()
    negative_flags = monthly_net < 0
    months_of_negative_flow = int(negative_flags.sum())

    longest_streak = 0
    current_streak = 0
    for is_neg in negative_flags:
        if is_neg:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

    return CashFlowFeatures(
        start_date=str(df["date"].min().date()),
        end_date=str(df["date"].max().date()),
        num_months=int(df["month"].nunique()),
        total_inflow=round(total_inflow, 2),
        total_outflow=round(total_outflow, 2),
        net_cash_flow=round(net_cash_flow, 2),
        monthly_revenue=monthly_revenue,
        revenue_volatility_pct=revenue_volatility_pct,
        largest_mom_drop_pct=largest_mom_drop_pct,
        largest_mom_drop_month=largest_mom_drop_month,
        top_customer_share_pct=top_customer_share_pct,
        top_customer_name=top_customer_name,
        top_3_customer_share_pct=top_3_customer_share_pct,
        num_unique_customers=num_unique_customers,
        seasonality_detected=seasonality_detected,
        seasonal_low_months=seasonal_low_months,
        seasonal_high_months=seasonal_high_months,
        monthly_expenses=monthly_expenses,
        expense_by_category=expense_by_category,
        avg_monthly_burn=avg_monthly_burn,
        months_of_negative_flow=months_of_negative_flow,
        longest_negative_streak_months=longest_streak,
    )
