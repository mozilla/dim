from textwrap import dedent

import yaml

from dim.app import prepare_params
from dim.models.dim_check_type.matches_regex import MatchesRegex
from dim.models.dim_config import DimConfig


def test_matches_regex():
    """Checking that sql is correctly generated for the matching regex check"""

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
          tier: tier_3
          dim_tests:
            - type: matches_regex
              params:
                columns:
                  - locale
                regex: ^23
        """
    )

    dim_config = DimConfig.from_dict(yaml.load(yaml_config, Loader=yaml.Loader)["dim_config"])

    dim_check = MatchesRegex(*table.split("."))
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
              COUNTIF(NOT REGEXP_CONTAINS(CAST(locale AS STRING), r"^23")) AS locale_regex_mismatch_count,  # noqa: E501
          FROM `dummy_project.dummy_dataset.dummy_table`
          WHERE DATE(submission_date) = DATE('1970-01-01')
      )

      SELECT
          'dummy_project' AS project_id,
          'dummy_dataset' AS dataset,
          'dummy_table' AS `table`,
          'tier_3' AS tier,
          DATE('1970-01-01') AS date_partition,
          'matches_regex' AS dim_check_type,
          '' AS dim_check_title,
          '' AS dim_check_description,
          IF(locale_regex_mismatch_count = 0, True, False) AS passed,
          \"""{"email": "dummy@mozilla.com", "slack": "dummy"}\""" AS owner,
          TO_JSON_STRING(CTE) AS query_results,
          TO_JSON_STRING(\"""{"regex": "^23","columns": "['locale']"}\""") AS dim_check_context,  # noqa: E501
          CAST('False' AS BOOL) AS alert_enabled,
          CAST('False' AS BOOL) AS alert_muted,
          'unit_test_run' AS run_id,
          TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), SECOND) AS actual_run_date,
          '[[dim_check_sql]]' AS dim_check_sql,
      FROM CTE"""
    )
    assert generated_sql == expected_sql.replace("  # noqa: E501", "")
