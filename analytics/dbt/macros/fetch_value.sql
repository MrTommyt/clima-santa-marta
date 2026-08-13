{% macro fetch_value(variable_name, variable_colname='variable', value_colname='value') -%}
    MAX({{ value_colname }}) FILTER (WHERE {{ variable_colname }} = {{ "'" ~ variable_name ~ "'" }}) AS {{ variable_name }}
{% endmacro -%}
