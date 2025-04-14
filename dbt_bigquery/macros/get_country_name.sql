{#
    This macro returns the corrected country name
#}

{% macro get_country_name(country) -%}

    case {{ dbt.safe_cast("country", api.Column.translate_type("string")) }}  
        when "United_States" then "United States"
        when "Russian_Federation" then "Russia"
        else country
    end

{%- endmacro %}