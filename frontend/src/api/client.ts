const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface Transaction {
  transaction_id: string;
  customer_id: string;
  merchant_id: string;
  amount: number;
  transaction_timestamp: string;
  currency: string;
  channel: string;
  city: string;
  is_international: boolean;
  hour?: number;
  day_of_week?: number;
  is_weekend?: boolean;
  amount_zscore?: number;
  anomaly_score?: number;
  is_anomaly?: number;
  anomaly_reasons?: string;
  merchant_name?: string;
  merchant_category?: string;
}

export interface PaginatedResponse {
  data: Transaction[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface AnomalyReason {
  reason: string;
  severity: number;
  detail: string;
}

export interface AnomalyExplanation {
  transaction_id: string;
  anomaly_score: number;
  reasons: AnomalyReason[];
}

export interface Stats {
  total_transactions: number;
  anomaly_count: number;
  anomaly_rate: number;
  avg_amount: number;
  top_categories: { category: string; count: number; avg_amount: number }[];
  daily_volume: { date: string; count: number; total_amount: number }[];
  anomalies_per_day: { date: string; count: number }[];
}

export interface CustomerHistory {
  customer_id: string;
  daily_history: { date: string; count: number; total_amount: number }[];
  stats: {
    avg_amount: number;
    std_amount: number;
    total_txns: number;
    usual_hours: string;
    has_international: boolean;
  };
}

export function getStats(): Promise<Stats> {
  return fetchJson("/api/stats");
}

export function getTransactions(params: Record<string, string>): Promise<PaginatedResponse> {
  const qs = new URLSearchParams(params).toString();
  return fetchJson(`/api/transactions?${qs}`);
}

export function getTransaction(id: string): Promise<Transaction> {
  return fetchJson(`/api/transactions/${id}`);
}

export function getAnomalies(page = 1, perPage = 20): Promise<PaginatedResponse> {
  return fetchJson(`/api/anomalies?page=${page}&per_page=${perPage}`);
}

export function getAnomalyExplanation(id: string): Promise<AnomalyExplanation> {
  return fetchJson(`/api/anomalies/${id}/explain`);
}

export function getCustomerHistory(customerId: string): Promise<CustomerHistory> {
  return fetchJson(`/api/customers/${customerId}/history`);
}

export async function retrainModel(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/model/retrain`, { method: "POST" });
  return res.json();
}
