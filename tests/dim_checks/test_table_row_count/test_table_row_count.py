from textwrap import dedent

import yaml

from dim.app import prepare_params
from dim.models.dim_check_type.table_row_count import TableRowCount
from dim.models.dim_config import DimConfig


def test_table_row_count():
    """Checking that sql is correctly generated for the table row count check"""  # noqa: E501

    table = "desination_project.destination_dataset.destination_table"

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
          tier: tier_3
          dim_tests:
            - type: table_row_count
              params:
                condition: ">= 1000"
        """
    )

    dim_config = DimConfig.from_dict(yaml.load(yaml_config, Loader=yaml.Loader)["dim_config"])

    dim_check = TableRowCount(*table.split("."))
    check_params = dim_config.dim_tests[0].params

    query_params = prepare_params(
        *table.split("."),
        dim_config=dim_config,
        alert_muted=False,
        check_params=check_params,
        run_uuid="unit_test_run",
        date_partition="1970-01-01",
    )
    generated_sql = dim_check.generate_test_sql(params=query_params)

    expected_sql = dedent(
        """\
          WITH CTE AS (
              SELECT
                  COUNT(*) AS row_count
              FROM `desination_project.destination_dataset.destination_table`
              WHERE DATE(submission_date) = DATE('1970-01-01')
          )

          SELECT
              'desination_project' AS project_id,
              'destination_dataset' AS dataset,
              'destination_table' AS `table`,
              'tier_3' AS tier,
              DATE('1970-01-01') AS date_partition,
              'table_row_count' AS dim_check_type,
              NULLIF('None', 'None') AS dim_check_title,
              NULLIF('Checking if the row count in the table is as expected.', 'None') AS dim_check_description,  # noqa: E501
              IF(row_count >= 1000, True, False) AS passed,
              '{"email": "dummy@mozilla.com", "slack": "dummy"}' AS owner,
              TO_JSON_STRING(CTE) AS query_results,
              TO_JSON_STRING("{'condition': '>= 1000'}") AS dim_check_context,
              CAST('False' AS BOOL) AS alert_enabled,
              CAST('False' AS BOOL) AS alert_muted,
              'unit_test_run' AS run_id,
              TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), SECOND) AS actual_run_date,
              '[[dim_check_sql]]' AS dim_check_sql,
          FROM CTE"""
    )
    assert generated_sql == expected_sql.replace("  # noqa: E501", "")
