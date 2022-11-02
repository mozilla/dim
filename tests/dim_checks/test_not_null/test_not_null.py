from textwrap import dedent

from dim.models.dq_checks.not_null import NotNull


def test_not_null_pass():
    """ """

    config = {
        "dim_config": {
            "owner": ["akommasani@mozilla.com"],
            "tests": [
                {
                    "type": "not_null",
                    "config": {
                        "columns": ["segment"],
                        "threshold": "row_count >= 1",
                    },
                }
            ],
        }
    }
    dq_check = NotNull(
        project_id="test_project",
        dataset="test_dataset",
        table="test_table",
        dataset_owner="akommasani@mozilla.com",
        config=config["dim_config"]["tests"][0]["config"],
        date="2022-01-13",
    )
    _, generated_sql = dq_check.generate_test_sql()

    expected_sql = dedent(
        """\
        WITH CTE AS (
            SELECT
                COUNT(*) AS row_count,
                segment,
            FROM `test_project.test_dataset.test_table`
            WHERE
                submission_date = DATE("2022-01-13")
                AND segment IS NULL
            GROUP BY
                segment
        )

        SELECT
            TO_JSON_STRING(CTE) AS additional_information,
            "test_project" AS project_id,
            "test_dataset" AS dataset,
            "test_table" AS table,
            "not_null" AS dq_check,
            "akommasani@mozilla.com" AS dataset_owner,
            "" AS slack_alert,
            CURRENT_DATETIME() AS created_date
        FROM CTE
        WHERE row_count >= 1"""
    )

    assert expected_sql == generated_sql
