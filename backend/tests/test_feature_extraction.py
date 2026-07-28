import io
import pytest
import pandas as pd

from app.services.feature_extraction import load_transactions, extract_features, InvalidTransactionData


def make_csv(rows: list[dict]) -> io.BytesIO:
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


def test_missing_required_column_raises():
    buf = make_csv([{"date": "2025-01-01", "amount": 100}])  # no counterparty
    with pytest.raises(InvalidTransactionData, match="counterparty"):
        load_transactions(buf)


def test_empty_csv_raises():
    buf = io.BytesIO(b"date,amount,counterparty\n")
    with pytest.raises(InvalidTransactionData):
        load_transactions(buf)


def test_unparseable_date_raises():
    buf = make_csv([{"date": "not-a-date", "amount": 100, "counterparty": "Acme"}])
    with pytest.raises(InvalidTransactionData):
        load_transactions(buf)


def test_top_customer_concentration_detected():
    rows = [
        {"date": "2025-01-05", "amount": 9000, "counterparty": "BigCo", "category": "revenue"},
        {"date": "2025-01-06", "amount": 1000, "counterparty": "SmallCo", "category": "revenue"},
    ]
    df = load_transactions(make_csv(rows))
    features = extract_features(df)
    assert features.top_customer_name == "BigCo"
    assert features.top_customer_share_pct == 90.0


def test_negative_flow_streak_detection():
    rows = [
        {"date": "2025-01-05", "amount": 100, "counterparty": "A", "category": "revenue"},
        {"date": "2025-01-06", "amount": -500, "counterparty": "vendor", "category": "rent"},
        {"date": "2025-02-05", "amount": 100, "counterparty": "A", "category": "revenue"},
        {"date": "2025-02-06", "amount": -500, "counterparty": "vendor", "category": "rent"},
        {"date": "2025-03-05", "amount": 1000, "counterparty": "A", "category": "revenue"},
    ]
    df = load_transactions(make_csv(rows))
    features = extract_features(df)
    assert features.months_of_negative_flow == 2
    assert features.longest_negative_streak_months == 2


def test_revenue_volatility_zero_when_flat():
    rows = [
        {"date": f"2025-0{m}-05", "amount": 1000, "counterparty": "A", "category": "revenue"}
        for m in range(1, 5)
    ]
    df = load_transactions(make_csv(rows))
    features = extract_features(df)
    assert features.revenue_volatility_pct == 0.0
