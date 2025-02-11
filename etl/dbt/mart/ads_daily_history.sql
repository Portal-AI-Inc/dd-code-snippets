
{#{{ config(#}
{#    materialized='table',#}
{#    indexes=[#}
{#        {'columns': ['ad_id', 'insight_date']},#}
{#    ]#}
{#)}}#}

with
  --
  facebook as
    (
      with
        -- todo consider adding platform_ad_id in the future
        insights as
          (
            select *
            from {{ ref('raw_airbyte_facebook_ads_insights') }}
          ),

        insight_actions as
          (
            select *
            from {{ ref('raw_airbyte_facebook_ads_insights_actions') }}
          ),

        insight_action_values as
          (
            select *
            from {{ ref('raw_airbyte_facebook_ads_insights_action_values') }}
          ),

        latest_insights as
          (
            -- this will be used for getting the latest campaign name for example
            with
              --
              insights_ranked as
                (
                  select *,
                         row_number() over (
                           partition by ad_id order by insight_date desc
                           ) as rn
                  from insights
                )

            select ir.*,
                a.is_active as adset_is_active,
                a.is_learning as adset_is_learning
            from insights_ranked ir
                 left join {{ ref('raw_airbyte_facebook_ad_sets') }} a
                           on ir.adset_id = a.id
            where rn = 1
          ),


        summary as
          (
            select ad_id,
                   insight_date,
                   gender,
                   age,

                   -- here sum is not really necessary it's more for a different group by like adset
                   sum(spend)       as cost,
                   sum(clicks)      as clicks,
                   sum(impressions) as impressions,
                   sum(reach) as reach,

                   -- here we should be more careful
                   avg(frequency) as frequency,
                   avg(ctr) as ctr,
                   -- avg(cpc) as cpc, -- we don't really need this
                   avg(cpm) as cpm
                   -- todo see if this can bu calculated after currency conversion ?
                   --avg(cost_per_inline_link_click) as cost_per_inline_link_click,

            from insights
            -- do not filter by cost > 0. there are values like conversions present
            group by ad_id, insight_date, gender, age
            order by ad_id, insight_date desc, gender, age
          ),


        daily_actions as
          (
            select ad_id,
                   insight_date,
                   gender,
                   age,
                   sum(value_omni_purchase)    as sum_purchase,
                   sum(value_omni_add_to_cart) as sum_add_to_cart,
                   sum(value_post_engagement)  as sum_post_engagement,
                   sum(value_link_click)       as sum_link_click,
                   sum(value_post)             as sum_post
            from insight_actions
            group by ad_id, insight_date, gender, age
          ),

        daily_action_values as
          (
            select ad_id,
                   insight_date,
                   gender,
                   age,
                   sum(value_omni_purchase)    as sum_purchase,
                   sum(value_omni_add_to_cart) as sum_add_to_cart
            from insight_action_values
            group by ad_id, insight_date, gender, age
          ),

        daily_metrics as
          (
            select li.ad_id,
                   da.insight_date,
                   da.gender,
                   da.age,

                   -- todo verify if should coalesce as 0

                   -- conversions
                   da.sum_purchase        as conversions,
                   dav.sum_purchase       as conversions_value,
                   -- adds to cart
                   da.sum_add_to_cart     as adds_to_cart,
                   dav.sum_add_to_cart    as adds_to_cart_value,
                   -- other metrics
                   da.sum_post_engagement as post_engagements,
                   da.sum_link_click      as link_clicks,
                   da.sum_post            as posts
            from latest_insights li
                   join daily_actions da
                        on li.ad_id = da.ad_id
                   join daily_action_values dav
                        on true
                          and li.ad_id = dav.ad_id
                          and da.insight_date = dav.insight_date
                          and da.gender = dav.gender
                          and da.age = dav.age
            -- NOTE these metrics have only been verified for sales campaigns
            -- where li.objective = 'OUTCOME_SALES' -- commenting out ! not sure what the consequences are
          ),

      video_p25 as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as video_view_p25
          from {{ ref('raw_airbyte_facebook_ads_insights_video_p25') }}
          group by ad_id, insight_date, gender, age
        ),

      video_p50 as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as video_view_p50
          from {{ ref('raw_airbyte_facebook_ads_insights_video_p50') }}
          group by ad_id, insight_date, gender, age
        ),
      video_p75 as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as video_view_p75
          from {{ ref('raw_airbyte_facebook_ads_insights_video_p75') }}
          group by ad_id, insight_date, gender, age
        ),
      video_p95 as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as video_view_p95
          from {{ ref('raw_airbyte_facebook_ads_insights_video_p95') }}
          group by ad_id, insight_date, gender, age
        ),
      video_p100 as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as video_view_p100
          from {{ ref('raw_airbyte_facebook_ads_insights_video_p100') }}
          group by ad_id, insight_date, gender, age
        ),
      video_avg as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 avg(value) as video_avg_play_time
          from {{ ref('raw_airbyte_facebook_ads_insights_video_avg_time') }}
          group by ad_id, insight_date, gender, age
        ),
      video_15s as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as thruplays
          from {{ ref('raw_airbyte_facebook_ads_insights_video_15s') }}
          group by ad_id, insight_date, gender, age
        ),
      video_plays as
        (
          select insight_date,
                 ad_id,
                 gender,
                 age,
                 sum(value) as video_n_plays
          from {{ ref('raw_airbyte_facebook_ads_insights_video_play_actions') }}
          group by ad_id, insight_date, gender, age
        ),

        merged as
          (
            select 'facebook'          as platform,
                   li.integration_id,
                   li.account_id,
                   li.campaign_id,
                   li.adset_id,
                   li.ad_id,
                   li.account_name,
                   li.campaign_name,
                   li.adset_name,
                   li.ad_name,
                   li.objective,
                   li.account_currency as currency,
                   li.adset_is_active,
                   li.adset_is_learning,
                   s.insight_date,
                   s.gender,
                   s.age,
                   s.cost,
                   s.impressions,
                   s.clicks,
                   s.reach,
                   s.frequency,
                   s.ctr,
                   s.cost / nullif(s.clicks, 0) as cost_per_click,
                   s.cpm,
                   -- s.cost_per_inline_link_click,
                   dm.conversions,
                   dm.conversions_value,
                   dm.adds_to_cart,
                   dm.adds_to_cart_value,
                   dm.post_engagements,
                   dm.link_clicks,
                   dm.posts,
                   v25.video_view_p25,
                   v50.video_view_p50,
                   v75.video_view_p75,
                   v95.video_view_p95,
                   v100.video_view_p100,
                   v_avg.video_avg_play_time,
                   v15s.thruplays,
                   v_plays.video_n_plays
            from latest_insights li
                   join summary s
                        on li.ad_id = s.ad_id
                   left join daily_metrics dm
                             on true
                               and li.ad_id = dm.ad_id
                               and s.insight_date = dm.insight_date
                               and s.gender = dm.gender
                               and s.age = dm.age
                   left join video_p25 v25
                             on true
                               and li.ad_id = v25.ad_id
                               and s.insight_date = v25.insight_date
                               and s.gender = v25.gender
                               and s.age = v25.age
                   left join video_p50 v50
                             on true
                               and li.ad_id = v50.ad_id
                               and s.insight_date = v50.insight_date
                               and s.gender = v50.gender
                               and s.age = v50.age
                   left join video_p75 v75
                             on true
                               and li.ad_id = v75.ad_id
                               and s.insight_date = v75.insight_date
                               and s.gender = v75.gender
                               and s.age = v75.age
                   left join video_p95 v95
                             on true
                               and li.ad_id = v95.ad_id
                               and s.insight_date = v95.insight_date
                               and s.gender = v95.gender
                               and s.age = v95.age
                   left join video_p100 v100
                             on true
                               and li.ad_id = v100.ad_id
                               and s.insight_date = v100.insight_date
                               and s.gender = v100.gender
                               and s.age = v100.age
                   left join video_avg v_avg
                             on true
                               and li.ad_id = v_avg.ad_id
                               and s.insight_date = v_avg.insight_date
                               and s.gender = v_avg.gender
                               and s.age = v_avg.age
                   left join video_15s v15s
                             on true
                               and li.ad_id = v15s.ad_id
                               and s.insight_date = v15s.insight_date
                               and s.gender = v15s.gender
                               and s.age = v15s.age
                   left join video_plays v_plays
                             on true
                               and li.ad_id = v_plays.ad_id
                               and s.insight_date = v_plays.insight_date
                               and s.gender = v_plays.gender
                               and s.age = v_plays.age
            --
          )


      select *
      from merged
    ),

  all_merged as
    (
      select *
      from facebook
      -- would do union all here
    ),

  currency_converted as (
    {{ convert_currency(
      'all_merged',
      'insight_date',
      'currency', [
        'cost',
        'conversions_value',
        'adds_to_cart_value',
        'cost_per_click',
      ]) }}
  )

select *
from currency_converted
order by insight_date desc,
         ad_id
