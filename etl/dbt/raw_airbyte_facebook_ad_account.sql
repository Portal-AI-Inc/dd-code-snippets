{# todo
    - check created_time format
#}

{%-
    set target_relation = adapter.get_relation(
        database=this.database,
        schema='public',
        identifier='airbyte_facebook_ad_account'
    )
-%}
{% set table_exists=target_relation is not none  %}
{% if table_exists %}
    select
        integration_id,
        account_id as id,
        id as facebook_account_id,
        name,
        business::json->>'id' as business_id,
        business::json->>'name' as business_name,
        case
            when business_name = '' then null
            else business_name
        end as business_name2,
        business_country_code,
        business_state,
        business_city,
        currency,
        timezone_id,
        timezone_name,
        timezone_offset_hours_utc,
        case
            when account_status::numeric = 1 then 'ACTIVE'
            when account_status::numeric = 2 then 'DISABLED'
            when account_status::numeric = 3 then 'UNSETTLED'
            when account_status::numeric = 7 then 'PENDING_RISK_REVIEW'
            when account_status::numeric = 8 then 'PENDING_SETTLEMENT'
            when account_status::numeric = 9 then 'IN_GRACE_PERIOD'
            when account_status::numeric = 100 then 'PENDING_CLOSURE'
            when account_status::numeric = 101 then 'CLOSED'
            when account_status::numeric = 201 then 'ANY_ACTIVE'
            when account_status::numeric = 202 then 'ANY_CLOSED'
            else null
        end as account_status,

        -- numeric -- todo add macros
        balance::numeric / 100 as balance,
        amount_spent::numeric / 100 as amount_spent,
        spend_cap::numeric / 100 as spend_cap,
        min_daily_budget::numeric / 100 as min_daily_budget,

        -- dates todo check if they need to be converted
        created_time

    from {{ source('raw', 'airbyte_facebook_ad_account') }}
{% else %}
    select
        null as integration_id,
        null as id,
        null as facebook_account_id,
        null as name,
        null as business_id,
        null as business_name,
        null as business_name2,
        null as business_country_code,
        null as business_state,
        null as business_city,
        null as currency,
        null as timezone_id,
        null as timezone_name,
        null as timezone_offset_hours_utc,
        null as account_status,

        -- numeric
        null::numeric as balance,
        null::numeric as amount_spent,
        null::numeric as spend_cap,
        null::numeric as min_daily_budget,

        -- dates
        null as created_time
    where false
{% endif %}