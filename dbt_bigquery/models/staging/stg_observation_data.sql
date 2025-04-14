{{
    config(
        materialized='view'
    )
}}

with observation_data as 
(
  select *
  from {{ source('staging','observation_external') }}
)
select



    cast(acq_timestamp as timestamp) as acq_timestamp,
    EXTRACT(YEAR from acq_timestamp) as acq_year,

    {{ get_country_name("country") }} as country,

    coalesce({{ dbt.safe_cast("type", api.Column.translate_type("integer")) }}, 0) as observation_type,
    {{ get_hot_spot_type("observation_type") }} as observation_type_description,

    brightness as brightness_kelvin,
    -- (brightness - 273.15) as brightness_celsius,
    -- ((brightness - 273.15) * 9 / 5 + 32) as brightness_fahrenheit,



    (scan * track) as area_km2,



from observation_data