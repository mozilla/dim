# dim test types

All tests need to have specific parameters provided via the `params` key in the config file to provide context around which specific columns to run the test on and for some tests we also need to provide success condition via the `condition` keyword.

## base

Abstract dim test type which contains all core logic around test SQL generation and execution. All dim test types inherit from it.

## column_length

Checks if the values in the specified columns follow specific length criteria.

params:

- `columns` - determines which columns in the table will be evaluated.
- `condition` - for example `"<= 2"` to indicate that the values should be 2 characters or less.

Example:

```yaml
- type: column_length
  params:
    columns:
      - country_code
    condition: "<= 2"
```

## not_null

Checks if the the specified columns contain any null values.

params:

- `columns` - determines which columns in the table will be evaluated.

Example:

```yaml
- type: not_null
  params:
    columns:
      - id
```

## table_row_count

Checks if the table has an expected number of columns.

params:

- `condition` - for example `"> 1000"` to indicate that the table should have more than 1000 rows.

Example:

```yaml
- type: table_row_count
  params:
    condition:  ">= 1"
```

## uniqueness

Checks if the values in the specified columns are unique (partition level only).

params:

- `columns` - determines which columns in the table will be evaluated.

Example:

```yaml
- type: uniqueness
  params:
    columns:
      - id
```

## value_in_set

Checks if the values in the specified columns contain only expected values.

params:

- `columns` - determines which columns in the table will be evaluated.
- `expected_values` - a list/set of values which we expect in these columns. Any other values will result in test failure.

Example:

```yaml
- type: value_in_set
  params:
    columns:
      - product_name
    expected_values:
      - product_1
      - product_2
```

## custom_sql_metric

A way to quickly write a custom check via arbitary SQL.

params:

- `sql` - Custom provided SQL which will be used to generate results.
- `condition` - How should we determine if the test is successful.

These template fields can be embedded inside the user provided `sql` param field which will be replaced with values at runtime:

- `{{ project_id }}` - project id of the table corresponding to the `dim_checks.yaml`.
- `{{ dataset }}` - dataset of the table corresponding to the `dim_checks.yaml`.
- `{{ table }}` - table of the table corresponding to the `dim_checks.yaml`.
- `{{ partition }}` - date partition for which the check is executed.

Example:

```yaml
- type: custom_sql_metric
  params:
    sql: |
      SELECT COUNT(*) AS total_count
      FROM `{{ project_id }}.{{ dataset }}.{{ table }}`
      WHERE project_id = '{{ project_id }}' AND DATE(date_partition) = '{{ partition }}'
    condition: total_count > 3000
```
