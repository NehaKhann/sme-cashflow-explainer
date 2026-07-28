import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_rejects_non_csv():
    resp = client.post(
        "/api/analyze",
        files={"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")},
    )
    assert resp.status_code == 400


def test_analyze_rejects_bad_schema():
    bad_csv = b"foo,bar\n1,2\n"
    resp = client.post(
        "/api/analyze",
        files={"file": ("data.csv", io.BytesIO(bad_csv), "text/csv")},
    )
    assert resp.status_code == 422


def test_analyze_happy_path():
    good_csv = (
        b"date,amount,counterparty,category\n"
        b"2025-01-05,9000,BigCo,revenue\n"
        b"2025-01-06,-500,vendor,rent\n"
        b"2025-02-05,9200,BigCo,revenue\n"
        b"2025-02-06,-500,vendor,rent\n"
    )
    resp = client.post(
        "/api/analyze",
        files={"file": ("data.csv", io.BytesIO(good_csv), "text/csv")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["top_customer_name"] == "BigCo"
    assert "narrative" in body
    assert body["risk_score"] >= 0
