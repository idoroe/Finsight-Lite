"""API route handlers."""

import json
import math
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from api.db import get_connection
from api.models import (
    AnomalyExplanation,
    AnomalyReason,
    PaginatedResponse,
    RetrainResponse,
    StatsResponse,
)

router = APIRouter(prefix="/api")

ROOT_DIR = Path(__file__).resolve().parent.parent


@router.get("/transactions", response_model=PaginatedResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    date_from: str | None = None,
    date_to: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    anomaly_only: bool = False,
):
    """Get paginated transactions with optional filters."""
    con = get_connection()
    conditions = []
    params: list = []

    if date_from:
        conditions.append("transaction_timestamp >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("transaction_timestamp <= ?")
        params.append(date_to)
    if amount_min is not None:
        conditions.append("amount >= ?")
        params.append(amount_min)
    if amount_max is not None:
        conditions.append("amount <= ?")
        params.append(amount_max)
    if anomaly_only:
        conditions.append("is_anomaly = 1")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Count total
    count_query = f"SELECT COUNT(*) FROM scored_transactions {where_clause}"
    total = con.execute(count_query, params).fetchone()[0]

    # Fetch page
    offset = (page - 1) * per_page
    data_query = f"""
        SELECT
            transaction_id, customer_id, merchant_id, amount,
            transaction_timestamp::VARCHAR as transaction_timestamp,
            currency, channel, city, is_international,
            hour, day_of_week, is_weekend,
            anomaly_score, is_anomaly, anomaly_reasons
        FROM scored_transactions
        {where_clause}
        ORDER BY transaction_timestamp DESC
        LIMIT {per_page} OFFSET {offset}
    """
    rows = con.execute(data_query, params).fetchall()
    columns = [
        "transaction_id", "customer_id", "merchant_id", "amount",
        "transaction_timestamp", "currency", "channel", "city", "is_international",
        "hour", "day_of_week", "is_weekend",
        "anomaly_score", "is_anomaly", "anomaly_reasons",
    ]

    data = []
    for row in rows:
        d = dict(zip(columns, row))
        d["is_international"] = bool(d["is_international"])
        d["is_weekend"] = bool(d.get("is_weekend"))
        data.append(d)

    con.close()

    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    """Get a single transaction by ID."""
    con = get_connection()
    row = con.execute("""
        SELECT
            s.transaction_id, s.customer_id, s.merchant_id, s.amount,
            s.transaction_timestamp::VARCHAR as transaction_timestamp,
            s.currency, s.channel, s.city, s.is_international,
            s.hour, s.day_of_week, s.is_weekend, s.amount_zscore,
            s.anomaly_score, s.is_anomaly, s.anomaly_reasons,
            m.merchant_name, m.merchant_category
        FROM scored_transactions s
        LEFT JOIN dim_merchant m ON s.merchant_id = m.merchant_id
        WHERE s.transaction_id = ?
    """, [transaction_id]).fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="Transaction not found")

    columns = [
        "transaction_id", "customer_id", "merchant_id", "amount",
        "transaction_timestamp", "currency", "channel", "city", "is_international",
        "hour", "day_of_week", "is_weekend", "amount_zscore",
        "anomaly_score", "is_anomaly", "anomaly_reasons",
        "merchant_name", "merchant_category",
    ]
    d = dict(zip(columns, row))
    d["is_international"] = bool(d["is_international"])
    d["is_weekend"] = bool(d.get("is_weekend"))
    return d


@router.get("/anomalies", response_model=PaginatedResponse)
def get_anomalies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Get anomalous transactions sorted by score descending."""
    con = get_connection()

    total = con.execute(
        "SELECT COUNT(*) FROM scored_transactions WHERE is_anomaly = 1"
    ).fetchone()[0]

    offset = (page - 1) * per_page
    rows = con.execute(f"""
        SELECT
            s.transaction_id, s.customer_id, s.merchant_id, s.amount,
            s.transaction_timestamp::VARCHAR as transaction_timestamp,
            s.currency, s.channel, s.city, s.is_international,
            s.anomaly_score, s.anomaly_reasons,
            m.merchant_name, m.merchant_category
        FROM scored_transactions s
        LEFT JOIN dim_merchant m ON s.merchant_id = m.merchant_id
        WHERE s.is_anomaly = 1
        ORDER BY s.anomaly_score DESC
        LIMIT {per_page} OFFSET {offset}
    """).fetchall()

    columns = [
        "transaction_id", "customer_id", "merchant_id", "amount",
        "transaction_timestamp", "currency", "channel", "city", "is_international",
        "anomaly_score", "anomaly_reasons", "merchant_name", "merchant_category",
    ]
    data = [dict(zip(columns, row)) for row in rows]
    for d in data:
        d["is_international"] = bool(d["is_international"])

    con.close()

    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/anomalies/{transaction_id}/explain", response_model=AnomalyExplanation)
def explain_anomaly(transaction_id: str):
    """Get top 3 explanation reasons for an anomaly."""
    con = get_connection()
    row = con.execute("""
        SELECT transaction_id, anomaly_score, anomaly_reasons
        FROM scored_transactions
        WHERE transaction_id = ? AND is_anomaly = 1
    """, [transaction_id]).fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    reasons_raw = row[2]
    reasons = json.loads(reasons_raw) if reasons_raw else []
    return AnomalyExplanation(
        transaction_id=row[0],
        anomaly_score=row[1],
        reasons=[AnomalyReason(**r) for r in reasons],
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Get summary statistics for the dashboard."""
    con = get_connection()

    # Basic stats
    stats = con.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as anomaly_count,
            AVG(amount) as avg_amount
        FROM scored_transactions
    """).fetchone()
    total, anomaly_count, avg_amount = stats

    # Top categories by transaction count
    top_cats = con.execute("""
        SELECT m.merchant_category, COUNT(*) as count, AVG(s.amount) as avg_amount
        FROM scored_transactions s
        LEFT JOIN dim_merchant m ON s.merchant_id = m.merchant_id
        GROUP BY m.merchant_category
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()

    # Daily volume
    daily = con.execute("""
        SELECT
            CAST(transaction_timestamp AS DATE) as date,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM scored_transactions
        GROUP BY CAST(transaction_timestamp AS DATE)
        ORDER BY date
    """).fetchall()

    # Anomalies per day
    anom_daily = con.execute("""
        SELECT
            CAST(transaction_timestamp AS DATE) as date,
            COUNT(*) as count
        FROM scored_transactions
        WHERE is_anomaly = 1
        GROUP BY CAST(transaction_timestamp AS DATE)
        ORDER BY date
    """).fetchall()

    con.close()

    return StatsResponse(
        total_transactions=total,
        anomaly_count=anomaly_count,
        anomaly_rate=round(anomaly_count / total * 100, 2) if total else 0,
        avg_amount=round(avg_amount, 2) if avg_amount else 0,
        top_categories=[
            {"category": c[0], "count": c[1], "avg_amount": round(c[2], 2)}
            for c in top_cats
        ],
        daily_volume=[
            {"date": str(d[0]), "count": d[1], "total_amount": round(d[2], 2)}
            for d in daily
        ],
        anomalies_per_day=[
            {"date": str(d[0]), "count": d[1]}
            for d in anom_daily
        ],
    )


@router.get("/customers/{customer_id}/history")
def get_customer_history(customer_id: str):
    """Get customer transaction history for sparkline (last 30 days)."""
    con = get_connection()

    # Daily spend for this customer
    daily = con.execute("""
        SELECT
            CAST(transaction_timestamp AS DATE) as date,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM scored_transactions
        WHERE customer_id = ?
        GROUP BY CAST(transaction_timestamp AS DATE)
        ORDER BY date
    """, [customer_id]).fetchall()

    # Customer stats
    stats = con.execute("""
        SELECT
            customer_avg_amount,
            customer_std_amount,
            customer_total_txns,
            customer_usual_hour_start,
            customer_usual_hour_end,
            has_international_history
        FROM dim_customer
        WHERE customer_id = ?
        LIMIT 1
    """, [customer_id]).fetchone()

    con.close()

    return {
        "customer_id": customer_id,
        "daily_history": [
            {"date": str(d[0]), "count": d[1], "total_amount": round(d[2], 2)}
            for d in daily
        ],
        "stats": {
            "avg_amount": round(stats[0], 2) if stats else 0,
            "std_amount": round(stats[1], 2) if stats else 0,
            "total_txns": stats[2] if stats else 0,
            "usual_hours": f"{int(stats[3])}:00–{int(stats[4])}:00" if stats else "N/A",
            "has_international": bool(stats[5]) if stats else False,
        } if stats else {},
    }


@router.post("/model/retrain", response_model=RetrainResponse)
def retrain_model():
    """Re-run the full pipeline: dbt + train + score + explain."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ml.run_pipeline"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return RetrainResponse(
                status="error",
                message=f"Pipeline failed: {result.stderr[:500]}",
            )
        return RetrainResponse(
            status="success",
            message="Pipeline completed successfully. Model retrained and scores updated.",
        )
    except subprocess.TimeoutExpired:
        return RetrainResponse(
            status="error",
            message="Pipeline timed out after 300 seconds.",
        )
