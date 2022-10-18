from textwrap import dedent

from dim.models.dq_checks.uniqueness import Uniqueness


def test_uniqueness_pass():
    """ """

    config = {
        "dim_config": {
            "owner": ["akommasani@mozilla.com"],
            "tests": [
                {
                    "type": "uniqueness",
                    "config": {
                        "columns": ["segment", "app_version"],
                        "threshold": "row_count >= 1",
                    },
                }
            ],
        }
    }
    dataset_owner = config["dim_config"]["owner"]
    dq_check = Uniqueness(
        project="test_project",
        dataset="test_dataset",
        table="test_table",
        config=config["dim_config"]["tests"][0]["config"],
        dataset_owner=dataset_owner,
        date_partition_parameter="2022-01-13",
    )
    _, generated_sql = dq_check.generate_test_sql()

    expected_sql = dedent(
        """
        WITH CTE AS (
            SELECT
                COUNT(*) AS row_count,
                segment,
                app_version,
            FROM `test_project.test_dataset.test_table`
            WHERE
            submission_date = DATE("2022-01-13")
            GROUP BY
            segment,app_version
            HAVING COUNT(*) > 1
        )

        SELECT
            TO_JSON_STRING(CTE) as additional_information,
            "test_project" as project,
            "test_dataset" as dataset,
            "test_table" as table,
            "uniqueness" as dq_check,
            "['akommasani@mozilla.com']" as dataset_owner,
            "" as slack_alert,
        CURRENT_DATETIME() as created_date
        FROM CTE
        WHERE row_count >= 1"""
    )

    assert (
        expected_sql.replace(" ", "").strip()
        == generated_sql.replace(" ", "").strip()
    )


test_uniqueness_pass()
