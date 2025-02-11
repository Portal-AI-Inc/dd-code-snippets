{%- set target_relation = adapter.get_relation(
    database=this.database,
    schema='public',
    identifier='airbyte_shopify_customer_journey_summary') -%}


{% set table_exists=target_relation is not none  %}

{% if table_exists %}
with customer_journey as
       (
         select *,
                customer_journey_summary::json as summary
         from airbyte_shopify_customer_journey_summary
       ),

     expanded as
       (
         select *,
                -- Extracting other top-level fields
                (summary ->> 'ready')                as ready,
                (summary ->> 'days_to_conversion')   as days_to_conversion,
                (summary ->> 'customer_order_index') as customer_order_index,

                -- extracting objects
                (summary -> 'moments_count')         as moments_count,
                (summary -> 'first_visit')           as first_visit,
                (summary -> 'last_visit')            as last_visit,
                (summary ->> 'moments')::json        as moments
         from customer_journey
       )

select integration_id,
       shop_url,
       {{ int_id_to_text('id') }}   as order_id, -- this is the same as order_id field
       created_at::timestamptz as created_at,
       updated_at::timestamptz as updated_at,
       ready,
       (days_to_conversion::numeric)::bigint as days_to_conversion,
       customer_order_index,
       moments_count ->> 'count'     as moment_count,
       moments_count ->> 'precision' as moment_count_precision,
       {{ json_with_id_or_null('first_visit') }} as first_visit,
       {{ json_with_id_or_null('last_visit') }} as last_visit,
       moments
from expanded

{% else %}
    select
        null as integration_id,
        null as shop_url,
	    null as order_id,
        null::timestamptz as created_at,
        null::timestamptz as updated_at,
        null::boolean as ready,
        null::bigint as days_to_conversion,
        null::bigint as customer_order_index,
        null::bigint as moments_count,
        null as moments_precision,
        null::json as first_visit,
        null::json as last_visit,
        null::jsonb as moments
    where false
{% endif %}
