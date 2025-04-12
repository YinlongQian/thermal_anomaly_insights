{{ config(materialized='table') }}

select 
    location,
    -- density_km2,
    -- density_mi2,
    -- population,
    land_area_km2,
    -- land_area_mi2

from {{ ref('population_density_lookup') }}