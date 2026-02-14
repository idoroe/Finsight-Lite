import type { Stats } from "../api/client";

interface Props {
  stats: Stats | null;
}

export default function StatsCards({ stats }: Props) {
  if (!stats) return <div className="stats-cards loading">Loading stats...</div>;

  const cards = [
    { label: "Total Transactions", value: stats.total_transactions.toLocaleString(), color: "#3b82f6" },
    { label: "Anomalies Detected", value: stats.anomaly_count.toLocaleString(), color: "#ef4444" },
    { label: "Anomaly Rate", value: `${stats.anomaly_rate}%`, color: "#f59e0b" },
    { label: "Avg Amount", value: `$${stats.avg_amount.toLocaleString()}`, color: "#10b981" },
  ];

  return (
    <div className="stats-cards">
      {cards.map((card) => (
        <div key={card.label} className="stat-card" style={{ borderTopColor: card.color }}>
          <div className="stat-value">{card.value}</div>
          <div className="stat-label">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
