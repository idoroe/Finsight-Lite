import { useNavigate } from "react-router-dom";
import type { Transaction } from "../api/client";

interface Props {
  transactions: Transaction[];
  loading: boolean;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function TransactionList({
  transactions,
  loading,
  page,
  totalPages,
  onPageChange,
}: Props) {
  const navigate = useNavigate();

  if (loading) return <div className="loading-spinner">Loading transactions...</div>;

  if (transactions.length === 0) {
    return <div className="empty-state">No transactions found.</div>;
  }

  return (
    <div className="transaction-list">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Timestamp</th>
            <th>Customer</th>
            <th>Amount</th>
            <th>Channel</th>
            <th>City</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr
              key={txn.transaction_id}
              className={txn.is_anomaly ? "anomaly-row" : ""}
              onClick={() =>
                txn.is_anomaly
                  ? navigate(`/anomalies/${txn.transaction_id}`)
                  : navigate(`/transactions`)
              }
              style={{ cursor: txn.is_anomaly ? "pointer" : "default" }}
            >
              <td>
                {txn.is_anomaly ? <span className="anomaly-icon">⚠</span> : null}
                {txn.transaction_id}
              </td>
              <td>{new Date(txn.transaction_timestamp).toLocaleString()}</td>
              <td>{txn.customer_id}</td>
              <td className="amount">
                ${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>
              <td>{txn.channel}</td>
              <td>
                {txn.city}
                {txn.is_international && <span className="intl-badge">INT</span>}
              </td>
              <td>
                {txn.anomaly_score != null
                  ? txn.anomaly_score.toFixed(3)
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          ← Prev
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
