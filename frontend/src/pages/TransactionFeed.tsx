import { useCallback, useEffect, useState } from "react";
import { getTransactions, type PaginatedResponse } from "../api/client";
import FilterBar from "../components/FilterBar";
import TransactionList from "../components/TransactionList";

export default function TransactionFeed() {
  const [txnData, setTxnData] = useState<PaginatedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const fetchTransactions = useCallback(
    async (p: number, f: Record<string, string>) => {
      setLoading(true);
      try {
        const data = await getTransactions({ ...f, page: String(p), per_page: "25" });
        setTxnData(data);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
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
    <div className="page transaction-feed">
      <h2>Transaction Feed</h2>
      <p className="subtitle">
        {txnData ? `${txnData.total.toLocaleString()} transactions` : "Loading..."}
      </p>
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
