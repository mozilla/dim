from textwrap import dedent

from dim.models.dim_config import DimConfig
from dim.models.dq_checks.uniqueness import Uniqueness


def test_uniqueness_pass():
    """ """

    config = DimConfig.from_dict(
        {
            "owner": ["akommasani@mozilla.com"],
            "tier": "tier_1",
            "dim_tests": [
                {
                    "type": "uniqueness",
                    "options": {
                        "columns": ["segment", "app_version"],
                        "threshold": "row_count >= 1",
                    },
                }
            ],
        }
    )

    dq_check = Uniqueness(
        project_id="test_project",
        dataset="test_dataset",
        table="test_table",
        dataset_owner="akommasani@mozilla.com",
        config=config.dim_tests[0].options,
        date="2022-01-13",
    )

    _, generated_sql = dq_check.generate_test_sql()

    expected_sql = dedent(
        """\
        WITH CTE AS (
            SELECT
                COUNT(*) AS row_count,
                segment,
                app_version,
            FROM `test_project.test_dataset.test_table`
            WHERE
                submission_date = DATE("2022-01-13")
            GROUP BY
                segment,
                app_version
            HAVING COUNT(*) > 1
        )

        SELECT
            TO_JSON_STRING(CTE) AS additional_information,
            "test_project" AS project_id,
            "test_dataset" AS dataset,
            "test_table" AS table,
            "uniqueness" AS dq_check,
            "akommasani@mozilla.com" AS dataset_owner,
            "" AS slack_alert,
            CURRENT_DATETIME() AS created_date
        FROM CTE
        WHERE row_count >= 1"""
    )

    assert generated_sql == expected_sql
