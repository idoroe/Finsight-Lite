"""Pydantic response models for the API."""

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    transaction_id: str
    customer_id: str
    merchant_id: str
    amount: float
    transaction_timestamp: str
    currency: str
    channel: str
    city: str
    is_international: bool
    hour: int | None = None
    day_of_week: int | None = None
    is_weekend: bool | None = None
    amount_zscore: float | None = None
    anomaly_score: float | None = None
    is_anomaly: int | None = None
    anomaly_reasons: str | None = None


class AnomalyReason(BaseModel):
    reason: str
    severity: float
    detail: str


class AnomalyExplanation(BaseModel):
    transaction_id: str
    anomaly_score: float
    reasons: list[AnomalyReason]


class StatsResponse(BaseModel):
    total_transactions: int
    anomaly_count: int
    anomaly_rate: float
    avg_amount: float
    top_categories: list[dict]
    daily_volume: list[dict]
    anomalies_per_day: list[dict]


class PaginatedResponse(BaseModel):
    data: list[dict]
    total: int
    page: int
    per_page: int
    pages: int


class RetrainResponse(BaseModel):
    status: str
    message: str
