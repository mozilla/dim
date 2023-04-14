from textwrap import dedent

import yaml

from dim.app import prepare_params
from dim.models.dim_check_type.column_length import ColumnLength
from dim.models.dim_config import DimConfig


def test_column_length():
    """Checking that sql is correctly generated for the column length"""

    table = "dummy_project.dummy_dataset.dummy_table"

    yaml_config = dedent(
        """
        dim_config:
          owner:
            email: akommasani@mozilla.com
            slack: alekhya
          alerts_enabled:
            enabled: true
            notify:
              channels:
                - dummy_channel
          partition_field: submission_date
          tier: tier_2
          dim_tests:
            - type: column_length
              params:
                columns:
                  - country
                condition: "= 2"
        """
    )

    dim_config = DimConfig.from_dict(yaml.load(yaml_config, Loader=yaml.Loader)["dim_config"])

    dim_check = ColumnLength(*table.split("."))
    check_params = dim_config.dim_tests[0].params

    query_params = prepare_params(
        *table.split("."),
        dim_config=dim_config,
        alert_muted=False,
        check_params=check_params,
        run_uuid="unit_test_run",
        date_partition="1990-01-01",
    )
    generated_sql = dim_check.generate_test_sql(params=query_params)

    expected_sql = dedent(
        """\
        WITH CTE AS (
            SELECT
                COUNTIF(NOT LENGTH(country) = 2 ) AS country_length_mismatch_count,
            FROM `dummy_project.dummy_dataset.dummy_table`
            WHERE
                DATE(submission_date) = DATE('1990-01-01')
        )

        SELECT
            'dummy_project' AS project_id,
            'dummy_dataset' AS dataset,
            'dummy_table' AS `table`,
            'tier_2' AS tier,
            DATE('1990-01-01') AS date_partition,
            'column_length' AS dim_check_type,
            IF(country_length_mismatch_count = 0, True, False) AS passed,
            '{"email": "akommasani@mozilla.com", "slack": "alekhya"}' AS owner,
            TO_JSON_STRING(CTE) AS query_results,
            TO_JSON_STRING("{'condition': '= 2', 'columns': '['country']") AS dim_check_context,  # noqa: E501
            CAST('False' AS BOOL) AS alert_enabled,
            CAST('False' AS BOOL) AS alert_muted,
            'unit_test_run' AS run_id,
            TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), SECOND) AS actual_run_date,
            '[[dim_check_sql]]' AS dim_check_sql,
        FROM CTE"""
    )
    assert generated_sql == expected_sql.replace("  # noqa: E501", "")
