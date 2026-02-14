with source as (
    select * from {{ source('raw', 'transactions') }}
)

select
    transaction_id,
    customer_id,
    merchant_id,
    merchant_name,
    merchant_category,
    cast(amount as double) as amount,
    cast(timestamp as timestamp) as transaction_timestamp,
    currency,
    channel,
    city,
    cast(is_international as boolean) as is_international
from source
