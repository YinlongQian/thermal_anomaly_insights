{#
    This macro returns the inferred hot spot type of the thermal anomaly
#}

{% macro get_hot_spot_type(observation_type) -%}

    case {{ dbt.safe_cast("type", api.Column.translate_type("integer")) }}  
        when 0 then 'presumed vegetation fire'
        when 1 then 'active volcano'
        when 2 then 'other static land source'
        when 3 then 'offshore'
        else 'unknown'
    end

{%- endmacro %}