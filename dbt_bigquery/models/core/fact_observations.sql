{{
    config(
        materialized = "table",
        tag=['partition_by_year'],
        partition_by = {
            "field": "acq_year",
            "data_type": "int64",
            "range": {
                "start": 2020,
                "end": 2023,
                "interval": 1
            }
        },
        require_partition_filter = true
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