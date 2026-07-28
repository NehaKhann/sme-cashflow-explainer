from __future__ import annotations

import pandas as pd

from ..models import CashFlowFeatures, InvalidTransactionData


REQUIRED_COLUMNS = {"date", "amount", "counterparty"}


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


def _compute_monthly_revenue(inflows: pd.DataFrame) -> pd.Series:
    return inflows.groupby("month")["amount"].sum().sort_index()


def _compute_revenue_volatility(monthly_rev: pd.Series) -> tuple[float, float, str | None]:
    if len(monthly_rev) < 2 or monthly_rev.mean() == 0:
        return 0.0, 0.0, None

    volatility = round(float(monthly_rev.std() / monthly_rev.mean() * 100), 1)

    pct_change = monthly_rev.pct_change() * 100
    if pct_change.dropna().empty:
        return volatility, 0.0, None

    largest_drop_idx = pct_change.idxmin()
    largest_drop_pct = round(float(pct_change.min()), 1)
    return volatility, largest_drop_pct, str(largest_drop_idx)


def _compute_customer_concentration(inflows: pd.DataFrame, total_inflow: float) -> tuple[str | None, float, float, int]:
    by_customer = inflows.groupby("counterparty")["amount"].sum().sort_values(ascending=False)
    num_unique = int(by_customer.shape[0])

    if total_inflow <= 0 or by_customer.empty:
        return None, 0.0, 0.0, num_unique

    top_name = str(by_customer.index[0])
    top_share = round(float(by_customer.iloc[0] / total_inflow * 100), 1)
    top3_share = round(float(by_customer.iloc[:3].sum() / total_inflow * 100), 1)
    return top_name, top_share, top3_share, num_unique


def _compute_seasonality(monthly_rev: pd.Series) -> tuple[bool, list, list]:
    low, high = [], []
    if len(monthly_rev) < 4:
        return False, low, high

    mean_rev = monthly_rev.mean()
    low_months = monthly_rev[monthly_rev < mean_rev * 0.8].index.tolist()
    high_months = monthly_rev[monthly_rev > mean_rev * 1.2].index.tolist()
    return bool(low_months or high_months), low_months, high_months


def _compute_expenses(outflows: pd.DataFrame) -> tuple[dict, dict, float]:
    monthly = outflows.groupby("month")["amount"].sum().abs().sort_index()
    monthly_expenses = {k: round(float(v), 2) for k, v in monthly.items()}
    avg_burn = round(float(monthly.mean()), 2) if not monthly.empty else 0.0

    by_cat = outflows.groupby("category")["amount"].sum().abs().sort_values(ascending=False)
    expense_by_category = {k: round(float(v), 2) for k, v in by_cat.items()}

    return monthly_expenses, expense_by_category, avg_burn


def _compute_negative_flow_streaks(df: pd.DataFrame) -> tuple[int, int]:
    monthly_net = df.groupby("month")["amount"].sum().sort_index()
    negative_flags = monthly_net < 0
    months_negative = int(negative_flags.sum())

    longest = 0
    current = 0
    for is_neg in negative_flags:
        if is_neg:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return months_negative, longest


def extract_features(df: pd.DataFrame) -> CashFlowFeatures:
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)

    inflows = df[df["amount"] > 0]
    outflows = df[df["amount"] < 0]

    total_inflow = float(inflows["amount"].sum())
    total_outflow = float(outflows["amount"].sum())
    net_cash_flow = float(df["amount"].sum())

    monthly_rev_series = _compute_monthly_revenue(inflows)
    monthly_revenue = {k: round(float(v), 2) for k, v in monthly_rev_series.items()}

    revenue_volatility_pct, largest_mom_drop_pct, largest_mom_drop_month = (
        _compute_revenue_volatility(monthly_rev_series)
    )

    top_customer_name, top_customer_share_pct, top_3_customer_share_pct, num_unique_customers = (
        _compute_customer_concentration(inflows, total_inflow)
    )

    seasonality_detected, seasonal_low_months, seasonal_high_months = (
        _compute_seasonality(monthly_rev_series)
    )

    monthly_expenses, expense_by_category, avg_monthly_burn = (
        _compute_expenses(outflows)
    )

    months_of_negative_flow, longest_negative_streak_months = (
        _compute_negative_flow_streaks(df)
    )

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
        longest_negative_streak_months=longest_negative_streak_months,
    )
