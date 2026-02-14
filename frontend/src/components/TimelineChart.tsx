import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Stats } from "../api/client";

interface Props {
  stats: Stats | null;
}

export default function TimelineChart({ stats }: Props) {
  if (!stats) return <div className="chart-placeholder">Loading chart...</div>;

  const anomalyMap = new Map(
    stats.anomalies_per_day.map((d) => [d.date, d.count])
  );

  const data = stats.daily_volume.map((d) => ({
    date: d.date.slice(5),
    volume: d.count,
    anomalies: anomalyMap.get(d.date) || 0,
  }));

  return (
    <div className="chart-container">
      <h3>Daily Transaction Volume & Anomalies</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="volume"
            fill="#3b82f620"
            stroke="#3b82f6"
            name="Transaction Volume"
          />
          <Bar
            yAxisId="right"
            dataKey="anomalies"
            fill="#ef4444"
            name="Anomalies"
            barSize={4}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
