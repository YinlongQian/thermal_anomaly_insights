{{
    config(
        materialized='table'
    )
}}

with observation_data as (
    select *
    from {{ ref('stg_observation_data') }}
), 
population_density as (
    select * 
    from {{ ref('population_density') }}
)
select
    *
from observation_data
inner join population_density
on observation_data.country = population_density.location