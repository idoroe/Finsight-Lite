import { useState } from "react";

interface Filters {
  date_from: string;
  date_to: string;
  amount_min: string;
  amount_max: string;
  anomaly_only: boolean;
}

interface Props {
  onFilter: (filters: Record<string, string>) => void;
}

export default function FilterBar({ onFilter }: Props) {
  const [filters, setFilters] = useState<Filters>({
    date_from: "",
    date_to: "",
    amount_min: "",
    amount_max: "",
    anomaly_only: false,
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (filters.amount_min) params.amount_min = filters.amount_min;
    if (filters.amount_max) params.amount_max = filters.amount_max;
    if (filters.anomaly_only) params.anomaly_only = "true";
    onFilter(params);
  }

  function handleReset() {
    setFilters({
      date_from: "",
      date_to: "",
      amount_min: "",
      amount_max: "",
      anomaly_only: false,
    });
    onFilter({});
  }

  return (
    <form className="filter-bar" onSubmit={handleSubmit}>
      <div className="filter-group">
        <label>From</label>
        <input
          type="date"
          value={filters.date_from}
          onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
        />
      </div>
      <div className="filter-group">
        <label>To</label>
        <input
          type="date"
          value={filters.date_to}
          onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
        />
      </div>
      <div className="filter-group">
        <label>Min $</label>
        <input
          type="number"
          placeholder="0"
          value={filters.amount_min}
          onChange={(e) => setFilters({ ...filters, amount_min: e.target.value })}
        />
      </div>
      <div className="filter-group">
        <label>Max $</label>
        <input
          type="number"
          placeholder="∞"
          value={filters.amount_max}
          onChange={(e) => setFilters({ ...filters, amount_max: e.target.value })}
        />
      </div>
      <div className="filter-group checkbox">
        <label>
          <input
            type="checkbox"
            checked={filters.anomaly_only}
            onChange={(e) =>
              setFilters({ ...filters, anomaly_only: e.target.checked })
            }
          />
          Anomalies Only
        </label>
      </div>
      <button type="submit" className="btn btn-primary">Apply</button>
      <button type="button" className="btn btn-secondary" onClick={handleReset}>
        Reset
      </button>
    </form>
  );
}
