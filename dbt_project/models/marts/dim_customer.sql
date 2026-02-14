with enriched as (
    select * from {{ ref('int_transactions_enriched') }}
)

select distinct
    customer_id,
    customer_avg_amount,
    customer_std_amount,
    customer_total_txns,
    customer_usual_hour_start,
    customer_usual_hour_end,
    max(case when is_international then 1 else 0 end) over (partition by customer_id) as has_international_history
from enriched
