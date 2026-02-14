import { useCallback, useEffect, useState } from "react";
import {
  getStats,
  getTransactions,
  type PaginatedResponse,
  type Stats,
} from "../api/client";
import FilterBar from "../components/FilterBar";
import StatsCards from "../components/StatsCards";
import TimelineChart from "../components/TimelineChart";
import TransactionList from "../components/TransactionList";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [txnData, setTxnData] = useState<PaginatedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const fetchTransactions = useCallback(
    async (p: number, f: Record<string, string>) => {
      setLoading(true);
      try {
        const data = await getTransactions({ ...f, page: String(p), per_page: "15" });
        setTxnData(data);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    getStats().then(setStats);
    fetchTransactions(1, {});
  }, [fetchTransactions]);

  function handleFilter(f: Record<string, string>) {
    setFilters(f);
    setPage(1);
    fetchTransactions(1, f);
  }

  function handlePageChange(p: number) {
    setPage(p);
    fetchTransactions(p, filters);
  }

  return (
    <div className="page dashboard">
      <h2>Dashboard</h2>
      <StatsCards stats={stats} />
      <TimelineChart stats={stats} />
      <FilterBar onFilter={handleFilter} />
      <TransactionList
        transactions={txnData?.data || []}
        loading={loading}
        page={page}
        totalPages={txnData?.pages || 0}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
