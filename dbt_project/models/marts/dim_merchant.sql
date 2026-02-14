with enriched as (
    select * from {{ ref('int_transactions_enriched') }}
)

select distinct
    merchant_id,
    merchant_name,
    merchant_category,
    merchant_avg_amount,
    merchant_unique_customers
from enriched
