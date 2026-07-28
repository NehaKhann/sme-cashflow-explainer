import io
import pytest

pytestmark = pytest.mark.asyncio


async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_analyze_rejects_non_csv(client):
    resp = await client.post(
        "/api/analyze",
        files={"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")},
    )
    assert resp.status_code == 400


async def test_analyze_rejects_bad_schema(client):
    bad_csv = b"foo,bar\n1,2\n"
    resp = await client.post(
        "/api/analyze",
        files={"file": ("data.csv", io.BytesIO(bad_csv), "text/csv")},
    )
    assert resp.status_code == 422


async def test_analyze_happy_path(client):
    good_csv = (
        b"date,amount,counterparty,category\n"
        b"2025-01-05,9000,BigCo,revenue\n"
        b"2025-01-06,-500,vendor,rent\n"
        b"2025-02-05,9200,BigCo,revenue\n"
        b"2025-02-06,-500,vendor,rent\n"
    )
    resp = await client.post(
        "/api/analyze",
        files={"file": ("data.csv", io.BytesIO(good_csv), "text/csv")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["top_customer_name"] == "BigCo"
    assert "narrative" in body
    assert body["risk_score"] >= 0
    assert "report_id" in body


async def test_reports_list_and_delete(client):
    good_csv = (
        b"date,amount,counterparty,category\n"
        b"2025-01-05,9000,BigCo,revenue\n"
        b"2025-02-05,9200,BigCo,revenue\n"
    )
    resp = await client.post(
        "/api/analyze",
        files={"file": ("data.csv", io.BytesIO(good_csv), "text/csv")},
    )
    assert resp.status_code == 200
    report_id = resp.json()["report_id"]

    list_resp = await client.get("/api/reports")
    assert list_resp.status_code == 200
    reports = list_resp.json()
    assert len(reports) == 1
    assert reports[0]["id"] == report_id

    detail_resp = await client.get(f"/api/reports/{report_id}")
    assert detail_resp.status_code == 200
    assert "raw_data" in detail_resp.json()

    del_resp = await client.delete(f"/api/reports/{report_id}")
    assert del_resp.status_code == 204
