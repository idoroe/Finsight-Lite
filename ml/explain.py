"""Generate human-readable anomaly explanations for flagged transactions."""

import json
import os
from pathlib import Path

import duckdb

DB_PATH = os.environ.get("DUCKDB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"))


def _get_customer_baselines(con: duckdb.DuckDBPyConnection) -> dict:
    """Get per-customer baselines for comparison."""
    rows = con.execute("""
        SELECT
            customer_id,
            customer_avg_amount,
            customer_std_amount,
            customer_usual_hour_start,
            customer_usual_hour_end,
            customer_total_txns,
            has_international_history
        FROM dim_customer
    """).fetchall()

    baselines = {}
    for row in rows:
        baselines[row[0]] = {
            "avg_amount": row[1],
            "std_amount": row[2],
            "usual_hour_start": row[3],
            "usual_hour_end": row[4],
            "total_txns": row[5],
            "has_international_history": bool(row[6]),
        }
    return baselines


def _get_customer_merchant_history(con: duckdb.DuckDBPyConnection) -> dict:
    """Get set of merchants each customer has transacted with."""
    rows = con.execute("""
        SELECT customer_id, merchant_id, count(*) as txn_count
        FROM fct_transactions
        GROUP BY customer_id, merchant_id
    """).fetchall()

    history: dict[str, dict[str, int]] = {}
    for cid, mid, cnt in rows:
        if cid not in history:
            history[cid] = {}
        history[cid][mid] = cnt
    return history


def _generate_reasons(txn: dict, baseline: dict, merchant_history: dict) -> list[dict]:
    """Generate all applicable reasons with severity scores."""
    reasons = []

    # 1. Unusual Amount
    if baseline["std_amount"] and baseline["std_amount"] > 0:
        zscore = abs((txn["amount"] - baseline["avg_amount"]) / baseline["std_amount"])
        if zscore > 2:
            ratio = txn["amount"] / baseline["avg_amount"] if baseline["avg_amount"] > 0 else 0
            severity = min(1.0, zscore / 10.0)
            reasons.append({
                "reason": "Unusual Amount",
                "severity": round(severity, 3),
                "detail": f"${txn['amount']:,.2f} is {ratio:.1f}x above this customer's average of ${baseline['avg_amount']:,.2f}",
            })

    # 2. Unusual Time
    hour = txn["hour"]
    usual_start = baseline["usual_hour_start"]
    usual_end = baseline["usual_hour_end"]
    if hour < usual_start or hour > usual_end:
        # How far outside normal hours
        distance = min(abs(hour - usual_start), abs(hour - usual_end))
        severity = min(1.0, distance / 12.0)
        hour_12 = hour % 12 or 12
        ampm = "AM" if hour < 12 else "PM"
        reasons.append({
            "reason": "Unusual Time",
            "severity": round(severity, 3),
            "detail": f"Transaction at {hour_12}:{txn.get('minute', 0):02d} {ampm}; customer typically transacts between {int(usual_start)}:00–{int(usual_end)}:00",
        })

    # 3. Rapid Transactions
    txn_count_hour = txn.get("txn_count_last_hour", 1)
    avg_hourly = baseline["total_txns"] / (90 * 24) if baseline["total_txns"] else 0
    if txn_count_hour >= 3 and (avg_hourly == 0 or txn_count_hour > avg_hourly * 5):
        severity = min(1.0, txn_count_hour / 10.0)
        reasons.append({
            "reason": "Rapid Transactions",
            "severity": round(severity, 3),
            "detail": f"{txn_count_hour} transactions in last hour (normal: {avg_hourly:.1f}/hr)",
        })

    # 4. New Merchant
    cid = txn["customer_id"]
    mid = txn["merchant_id"]
    customer_merchants = merchant_history.get(cid, {})
    is_first = customer_merchants.get(mid, 0) <= 1
    if is_first and txn.get("is_new_merchant"):
        severity = 0.4
        reasons.append({
            "reason": "New Merchant",
            "severity": severity,
            "detail": f"First transaction at {txn.get('merchant_name', mid)} — category: {txn.get('merchant_category', 'Unknown')}",
        })

    # 5. Unusual International Activity
    if txn.get("is_international") and not baseline.get("has_international_history"):
        severity = 0.8
        reasons.append({
            "reason": "Unusual International Activity",
            "severity": severity,
            "detail": f"International transaction from {txn.get('city', 'Unknown')} — no prior international history",
        })

    # Sort by severity descending, return top 3
    reasons.sort(key=lambda r: r["severity"], reverse=True)
    return reasons[:3]


def explain():
    """Generate explanations for all anomalous transactions."""
    con = duckdb.connect(DB_PATH)

    customer_baselines = _get_customer_baselines(con)
    merchant_history = _get_customer_merchant_history(con)

    # Get anomalous transactions with details
    anomalies = con.execute("""
        SELECT
            s.transaction_id,
            s.customer_id,
            s.merchant_id,
            s.amount,
            s.hour,
            extract(minute from s.transaction_timestamp) as minute,
            s.is_international,
            s.is_new_merchant,
            s.txn_count_last_hour,
            s.amount_zscore,
            s.city,
            s.anomaly_score,
            m.merchant_name,
            m.merchant_category
        FROM scored_transactions s
        LEFT JOIN dim_merchant m ON s.merchant_id = m.merchant_id
        WHERE s.is_anomaly = 1
    """).fetchall()

    columns = [
        "transaction_id", "customer_id", "merchant_id", "amount", "hour",
        "minute", "is_international", "is_new_merchant", "txn_count_last_hour",
        "amount_zscore", "city", "anomaly_score", "merchant_name", "merchant_category",
    ]

    explained_count = 0
    for row in anomalies:
        txn = dict(zip(columns, row))
        cid = txn["customer_id"]
        baseline = customer_baselines.get(cid, {
            "avg_amount": 0, "std_amount": 0,
            "usual_hour_start": 9, "usual_hour_end": 17,
            "total_txns": 0, "has_international_history": False,
        })

        reasons = _generate_reasons(txn, baseline, merchant_history)
        if not reasons:
            reasons = [{
                "reason": "Statistical Outlier",
                "severity": 0.5,
                "detail": f"Transaction scored as anomalous (score: {txn['anomaly_score']:.3f}) based on combined feature analysis",
            }]

        reasons_json = json.dumps(reasons)
        con.execute(
            "UPDATE scored_transactions SET anomaly_reasons = ? WHERE transaction_id = ?",
            [reasons_json, txn["transaction_id"]],
        )
        explained_count += 1

    con.close()
    print(f"Generated explanations for {explained_count} anomalous transactions")


if __name__ == "__main__":
    explain()
