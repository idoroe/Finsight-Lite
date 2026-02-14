import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getAnomalyExplanation,
  getCustomerHistory,
  getTransaction,
  type AnomalyExplanation,
  type CustomerHistory,
  type Transaction,
} from "../api/client";

export default function AnomalyDetail() {
  const { id } = useParams<{ id: string }>();
  const [txn, setTxn] = useState<Transaction | null>(null);
  const [explanation, setExplanation] = useState<AnomalyExplanation | null>(null);
  const [history, setHistory] = useState<CustomerHistory | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    getTransaction(id).then(setTxn).catch(() => setError("Transaction not found"));
    getAnomalyExplanation(id).then(setExplanation).catch(() => {});
  }, [id]);

  useEffect(() => {
    if (!txn) return;
    getCustomerHistory(txn.customer_id).then(setHistory).catch(() => {});
  }, [txn]);

  if (error) {
    return (
      <div className="page anomaly-detail">
        <div className="error-state">{error}</div>
        <Link to="/" className="btn btn-secondary">← Back to Dashboard</Link>
      </div>
    );
  }

  if (!txn || !explanation) {
    return <div className="page anomaly-detail loading">Loading anomaly details...</div>;
  }

  const scorePercent = Math.round((explanation.anomaly_score || 0) * 100);

  return (
    <div className="page anomaly-detail">
      <Link to="/" className="back-link">← Back to Dashboard</Link>

      <div className="anomaly-header">
        <div className="anomaly-badge">ANOMALY DETECTED</div>
        <h2>{txn.transaction_id}</h2>
        <div className="score-display">
          <div className="score-ring" style={{
            background: `conic-gradient(#ef4444 ${scorePercent}%, #e5e7eb ${scorePercent}%)`,
          }}>
            <div className="score-inner">{scorePercent}%</div>
          </div>
          <span className="score-label">Anomaly Score</span>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-section reasons-section">
          <h3>Top Anomaly Reasons</h3>
          <div className="reasons-list">
            {explanation.reasons.map((reason, i) => (
              <div key={i} className="reason-card">
                <div className="reason-header">
                  <span className="reason-rank">#{i + 1}</span>
                  <span className="reason-title">{reason.reason}</span>
                  <span className="reason-severity">
                    {Math.round(reason.severity * 100)}%
                  </span>
                </div>
                <div className="severity-bar-track">
                  <div
                    className="severity-bar-fill"
                    style={{
                      width: `${reason.severity * 100}%`,
                      backgroundColor:
                        reason.severity > 0.7
                          ? "#ef4444"
                          : reason.severity > 0.4
                          ? "#f59e0b"
                          : "#3b82f6",
                    }}
                  />
                </div>
                <p className="reason-detail">{reason.detail}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="detail-section info-section">
          <h3>Transaction Details</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Amount</span>
              <span className="info-value">
                ${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                {" "}{txn.currency}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Customer</span>
              <span className="info-value">{txn.customer_id}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Merchant</span>
              <span className="info-value">
                {txn.merchant_name || txn.merchant_id}
                {txn.merchant_category && (
                  <span className="category-tag">{txn.merchant_category}</span>
                )}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Timestamp</span>
              <span className="info-value">
                {new Date(txn.transaction_timestamp).toLocaleString()}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Channel</span>
              <span className="info-value">{txn.channel}</span>
            </div>
            <div className="info-item">
              <span className="info-label">City</span>
              <span className="info-value">
                {txn.city}
                {txn.is_international && <span className="intl-badge">International</span>}
              </span>
            </div>
          </div>
        </div>
      </div>

      {history && (
        <div className="detail-section customer-section">
          <h3>Customer Profile — {txn.customer_id}</h3>
          <div className="customer-stats">
            <div className="cstat">
              <span className="cstat-value">${history.stats.avg_amount.toLocaleString()}</span>
              <span className="cstat-label">Avg Spend</span>
            </div>
            <div className="cstat">
              <span className="cstat-value">{history.stats.total_txns}</span>
              <span className="cstat-label">Total Txns</span>
            </div>
            <div className="cstat">
              <span className="cstat-value">{history.stats.usual_hours}</span>
              <span className="cstat-label">Usual Hours</span>
            </div>
            <div className="cstat">
              <span className="cstat-value">
                {history.stats.has_international ? "Yes" : "No"}
              </span>
              <span className="cstat-label">International</span>
            </div>
          </div>

          <h4>Daily Spending (Last 90 Days)</h4>
          <ResponsiveContainer width="100%" height={150}>
            <AreaChart data={history.daily_history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="total_amount"
                stroke="#3b82f6"
                fill="#3b82f620"
                name="Daily Spend"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
