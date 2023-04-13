from textwrap import dedent

import yaml

from dim.app import prepare_params
from dim.models.dim_check_type.custom_sql_metric import CustomSqlMetric
from dim.models.dim_config import DimConfig


def test_custom_sql():
    """Checking that sql is correctly generated for the custom sql metrics"""

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
            - type: custom_sql_metric
              params:
                sql: |
                  SELECT COUNT(*) AS count
                  FROM `{{ project_id }}.{{ dataset }}.{{ table }}`
                  WHERE project_id = "data-monitoring-dev"
                condition: "count = 0"
                """
    )

    dim_config = DimConfig.from_dict(yaml.load(yaml_config, Loader=yaml.Loader)["dim_config"])

    dim_check = CustomSqlMetric(*table.split("."))
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
        """\
      WITH CTE AS (
          SELECT COUNT(*) AS count
      FROM `dummy_project.dummy_dataset.dummy_table`
      WHERE project_id = "data-monitoring-dev"
      )

      SELECT
          'dummy_project' AS project_id,
          'dummy_dataset' AS dataset,
          'dummy_table' AS table,
          'tier_2' AS tier,
          'custom_sql_metric' AS dim_check_type,
          DATE('1990-01-01') AS date_partition,
          IF(count = 0, True, False) AS passed,
          '{"email": "dummy@mozilla.com", "slack": "dummy"}' AS owner,
          TO_JSON_STRING(CTE) AS query_results,
          TO_JSON_STRING("{'condition': 'count = 0'") AS dim_check_context,
          CAST('False' AS BOOL) AS alert_enabled,
          CAST('False' AS BOOL) AS alert_muted,
          'unit_test_run' AS run_id,
          TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), SECOND) AS actual_run_date,
          '[[dim_check_sql]]' AS dim_check_sql,
      FROM CTE"""
    )
    assert generated_sql == expected_sql.replace("  # noqa: E501", "")
