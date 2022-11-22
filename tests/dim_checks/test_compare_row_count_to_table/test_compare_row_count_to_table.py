from textwrap import dedent

import yaml

from dim.app import prepare_params
from dim.models.dim_check_type.compare_row_count_to_table import (
    CompareRowCountToTable,
)
from dim.models.dim_config import DimConfig


def test_compare_row_count_to_table():
    """Checking that sql is correctly generated for the compare row count to table check"""  # noqa: E501

    table = "dummy_project.dummy_dataset.dummy_table"

    yaml_config = dedent(
        """
        dim_config:
          owner:
            email: dummy@mozilla.com
            slack: dummy
          alerts_enabled:
            enabled: true
            notify:
              channels:
                - dummy_channel
          partition_field: submission_date
          tier: tier_2
          dim_tests:
            - type: compare_row_count_to_table
              params:
                table: dummy2_project.dummy2_dataset.dummy2_table
                table_partition_field: submission_date2
        """
    )

    dim_config = DimConfig.from_dict(
        yaml.load(yaml_config, Loader=yaml.Loader)["dim_config"]
    )

    dim_check = CompareRowCountToTable(*table.split("."))
    check_params = dim_config.dim_tests[0].params

    query_params = prepare_params(
        *table.split("."),
        dim_config=dim_config,
        alert_muted=False,
        check_params=check_params,
        run_uuid="unit_test_run",
        date_partition="1990-01-01",
    )
    _, generated_sql = dim_check.generate_test_sql(params=query_params)

    expected_sql = dedent(
        """
        WITH CTE AS (
            SELECT
                (SELECT COUNT(*) FROM `dummy_project.dummy_dataset.dummy_table` WHERE DATE(submission_date) = DATE('1990-01-01')) AS row_count,  # noqa: E501
                (SELECT COUNT(*) FROM `dummy2_project.dummy2_dataset.dummy2_table` WHERE DATE(submission_date2) = DATE('1990-01-01')) AS dummy2_table_row_count,  # noqa: E501
        )

        SELECT
            'dummy_project' AS project_id,
            'dummy_dataset' AS dataset,
            'dummy_table' AS table,
            'tier_2' AS tier,
            DATE('1990-01-01') AS date_partition,
            'compare_row_count_to_table' AS dim_check_type,
            IF(row_count = dummy2_table_row_count, True, False) AS passed,
            '{"email": "dummy@mozilla.com", "slack": "dummy"}' AS owner,
            TO_JSON_STRING(CTE) AS query_results,
            TO_JSON_STRING('{"other_table":"dummy2_project.dummy2_dataset.dummy2_table", "other_table_partition_field": "submission_date2"}') AS dim_check_context,  # noqa: E501
            CAST('False' AS BOOL) AS alert_enabled,
            CAST('False' AS BOOL) AS alert_muted,
            'unit_test_run' AS run_id,
            TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), SECOND) AS actual_run_date,
            '[[dim_check_sql]]' AS dim_check_sql,
        FROM CTE"""
    )
    assert generated_sql == expected_sql.replace("  # noqa: E501", "")
