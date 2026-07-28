from app.services.feature_extraction import CashFlowFeatures
from app.services.risk_scoring import assess_risk


def _base_features(**overrides) -> CashFlowFeatures:
    defaults = dict(
        start_date="2025-01-01", end_date="2025-12-31", num_months=12,
        total_inflow=100000, total_outflow=-90000, net_cash_flow=10000,
        monthly_revenue={}, revenue_volatility_pct=10.0,
        largest_mom_drop_pct=-5.0, largest_mom_drop_month="2025-06",
        top_customer_share_pct=15.0, top_customer_name="Acme",
        top_3_customer_share_pct=40.0, num_unique_customers=10,
        seasonality_detected=False, seasonal_low_months=[], seasonal_high_months=[],
        monthly_expenses={}, expense_by_category={}, avg_monthly_burn=7500,
        months_of_negative_flow=0, longest_negative_streak_months=0,
    )
    defaults.update(overrides)
    return CashFlowFeatures(**defaults)


def test_low_risk_business_scores_low():
    features = _base_features()
    risk = assess_risk(features)
    assert risk.overall_band == "low"
    assert risk.flags[0].code == "NO_MAJOR_FLAGS"


def test_high_concentration_triggers_high_flag():
    features = _base_features(top_customer_share_pct=70.0)
    risk = assess_risk(features)
    codes = [f.code for f in risk.flags]
    assert "CUSTOMER_CONCENTRATION" in codes
    high_flags = [f for f in risk.flags if f.code == "CUSTOMER_CONCENTRATION"]
    assert high_flags[0].severity == "high"


def test_sustained_negative_flow_triggers_high_risk():
    features = _base_features(longest_negative_streak_months=4, months_of_negative_flow=4)
    risk = assess_risk(features)
    codes = [f.code for f in risk.flags]
    assert "SUSTAINED_NEGATIVE_FLOW" in codes
    assert risk.overall_band in ("medium", "high")


def test_score_capped_at_100():
    features = _base_features(
        revenue_volatility_pct=90.0,
        top_customer_share_pct=90.0,
        longest_negative_streak_months=6,
        months_of_negative_flow=6,
        largest_mom_drop_pct=-60.0,
        num_unique_customers=2,
    )
    risk = assess_risk(features)
    assert risk.overall_score <= 100
    assert risk.overall_band == "high"
