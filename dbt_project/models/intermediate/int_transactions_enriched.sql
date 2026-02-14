with txn as (
    select * from {{ ref('stg_transactions') }}
),

customer_stats as (
    select
        customer_id,
        avg(amount) as customer_avg_amount,
        stddev(amount) as customer_std_amount,
        count(*) as customer_total_txns,
        min(extract(hour from transaction_timestamp)) as customer_usual_hour_start,
        max(extract(hour from transaction_timestamp)) as customer_usual_hour_end
    from txn
    group by customer_id
),

merchant_stats as (
    select
        merchant_id,
        avg(amount) as merchant_avg_amount,
        count(distinct customer_id) as merchant_unique_customers
    from txn
    group by merchant_id
),

customer_merchants as (
    select distinct
        customer_id,
        merchant_id
    from txn
),

txn_with_lag as (
    select
        t.*,
        lag(t.transaction_timestamp) over (
            partition by t.customer_id order by t.transaction_timestamp
        ) as prev_transaction_timestamp,
        count(*) over (
            partition by t.customer_id
            order by t.transaction_timestamp
            range between interval 60 minutes preceding and current row
        ) as txn_count_last_hour
    from txn t
)

select
    t.transaction_id,
    t.customer_id,
    t.merchant_id,
    t.merchant_name,
    t.merchant_category,
    t.amount,
    t.transaction_timestamp,
    t.currency,
    t.channel,
    t.city,
    t.is_international,

    -- Time features
    extract(hour from t.transaction_timestamp) as hour,
    extract(dow from t.transaction_timestamp) as day_of_week,
    case when extract(dow from t.transaction_timestamp) in (0, 6) then true else false end as is_weekend,

    -- Amount z-score
    case
        when cs.customer_std_amount > 0
        then (t.amount - cs.customer_avg_amount) / cs.customer_std_amount
        else 0
    end as amount_zscore,

    -- Time since last transaction (minutes)
    case
        when t.prev_transaction_timestamp is not null
        then extract(epoch from (t.transaction_timestamp - t.prev_transaction_timestamp)) / 60.0
        else null
    end as time_since_last_txn,

    -- Is new merchant for this customer
    case
        when cm_prior.merchant_id is null then true
        else false
    end as is_new_merchant,

    -- Transaction count in last hour
    t.txn_count_last_hour,

    -- Customer stats
    cs.customer_avg_amount,
    cs.customer_std_amount,
    cs.customer_total_txns,
    cs.customer_usual_hour_start,
    cs.customer_usual_hour_end,

    -- Merchant stats
    ms.merchant_avg_amount,
    ms.merchant_unique_customers

from txn_with_lag t
left join customer_stats cs on t.customer_id = cs.customer_id
left join merchant_stats ms on t.merchant_id = ms.merchant_id
left join customer_merchants cm_prior
    on t.customer_id = cm_prior.customer_id
    and t.merchant_id = cm_prior.merchant_id
