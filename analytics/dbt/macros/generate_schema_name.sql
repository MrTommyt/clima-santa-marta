{#
  dbt's default appends the custom schema to the profile schema
  ("gold_staging"). Override: a model's +schema is the literal schema name,
  so staging lands in "staging" and marts in "gold".
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
