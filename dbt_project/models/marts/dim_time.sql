with dates as (
    select distinct
        cast(transaction_timestamp as date) as date_key,
        extract(year from transaction_timestamp) as year,
        extract(month from transaction_timestamp) as month,
        extract(day from transaction_timestamp) as day,
        extract(dow from transaction_timestamp) as day_of_week,
        case when extract(dow from transaction_timestamp) in (0, 6) then true else false end as is_weekend,
        extract(quarter from transaction_timestamp) as quarter
    from {{ ref('stg_transactions') }}
)

select * from dates
order by date_key
