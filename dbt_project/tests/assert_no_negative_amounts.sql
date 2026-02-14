-- Custom test: ensure no transactions have negative amounts
select
    transaction_id,
    amount
from {{ ref('fct_transactions') }}
where amount < 0
