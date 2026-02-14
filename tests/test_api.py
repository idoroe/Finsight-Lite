"""Tests for the FastAPI endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_stats_returns_expected_keys():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    expected_keys = {
        "total_transactions", "anomaly_count", "anomaly_rate",
        "avg_amount", "top_categories", "daily_volume", "anomalies_per_day",
    }
    assert expected_keys == set(data.keys())
    assert data["total_transactions"] == 50000
    assert data["anomaly_count"] > 0
    assert data["anomaly_rate"] > 0


def test_anomalies_sorted_and_have_reasons():
    response = client.get("/api/anomalies?per_page=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["data"]) <= 10

    # Check sorted by anomaly_score descending
    scores = [d["anomaly_score"] for d in data["data"]]
    assert scores == sorted(scores, reverse=True)

    # Check all have anomaly_reasons
    for d in data["data"]:
        assert d["anomaly_reasons"] is not None
        reasons = json.loads(d["anomaly_reasons"])
        assert len(reasons) > 0
        assert "reason" in reasons[0]
        assert "severity" in reasons[0]
        assert "detail" in reasons[0]


def test_transactions_pagination():
    response = client.get("/api/transactions?page=1&per_page=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 5
    assert data["page"] == 1
    assert data["per_page"] == 5
    assert data["total"] == 50000


def test_transactions_filter_anomaly_only():
    response = client.get("/api/transactions?anomaly_only=true&per_page=5")
    assert response.status_code == 200
    data = response.json()
    for txn in data["data"]:
        assert txn["is_anomaly"] == 1


def test_get_single_transaction():
    # First get an ID
    response = client.get("/api/transactions?per_page=1")
    txn_id = response.json()["data"][0]["transaction_id"]

    response = client.get(f"/api/transactions/{txn_id}")
    assert response.status_code == 200
    assert response.json()["transaction_id"] == txn_id


def test_anomaly_explain():
    # Get an anomaly ID
    response = client.get("/api/anomalies?per_page=1")
    txn_id = response.json()["data"][0]["transaction_id"]

    response = client.get(f"/api/anomalies/{txn_id}/explain")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == txn_id
    assert data["anomaly_score"] > 0
    assert len(data["reasons"]) > 0


def test_transaction_not_found():
    response = client.get("/api/transactions/TXN-DOESNOTEXIST")
    assert response.status_code == 404
