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

## compare_row_count_to_table

Compares if the table's row count is the same as another table's row count. The test fails if the row counts are different.

params:
- `table` - Table to check the row count against (must be fully qualified table name: `project_id.dataset.table`).
- `partition_field` - field used as a partition field in the other table.

Example:

```yaml
- type: compare_row_count_to_table
      params:
        table: moz-fx-data-shared-prod.internet_outages.global_outages_v1
        table_partition_field: datetime
```

## combined_column_uniqueness

Checks if a column combination is unique.

params:
- `columns` - columns which should provide a unique combination.

Example:

```yaml
- type: combined_column_uniqueness
  params:
    columns:
      - project_id
      - dataset
      - table
      - date_partition
```

## matches_regex

Checks if the columns conform to the provided regex rules.

params:
- `columns` - columns which will be compared against the regex.
- `regex` - regex which will be used for value structure validation.


Example:

```yaml
- type: matches_regex
  params:
    columns:
      - locale
    regex: ^[a-z]{2}-[A-Z]{2}$  # example: en-GB
```

_Note_ Due to some issues, as a workaround the regex stored inside `dim_check_context` (`dim_run_history_v1` table) contains double escape characters. Actual regex used only one, so the example above would looks like this in the table: `^\\w{2}-\\w{2}$` instead of `^\w{2}-\w{2}$`.

## numeric_value_matches

Checks that the numeric values are as expected. This could be used to check if the values are equal to, great, less than, or within a numeric range.

params:
- `columns` - columns which values will be compared against the condition.
- `condition` - defines condition the values must meet in order for the test to pass.

Example:

```yaml
- type: numeric_values_matches
      params:
        columns:
          - year
        condition: "> 2020"
```

## previous_count_avg_within_expected_delta

Checks that the row count of the partition checked is within an expected value range in comparison to past partitions. Average row count for x day partitions is calculated and min and max row_count values are calculated:
date_range_avg_row_count +/- `(date_range_avg_row_count / 100 * {{ params.expected_delta }})`. If the checked partition row count is within (min and max inclusive) this range the test passes.

`Disclaimer`: can only be used with tables, does not work with views!

params:
- `days` - number of past day partitions to use to calculate row count average.
- `expected_delta` - expected percentage difference between the current partition's row_count and the past x days average.

```yaml
- type: previous_count_avg_within_expected_delta
      params:
        days: 7
        expected_delta: 5
```