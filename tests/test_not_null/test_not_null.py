from dim.models.dq_checks.not_null import NotNull
import json
from textwrap import dedent


def test_not_null_pass():
        """ """
        
        config = {'dim_config': {'owner': ['akommasani@mozilla.com'], 'tests': [{'type': 'not_null', 'config': {'columns':['segment'],'threshold': 'row_count >= 1'}}]}}
        dataset_owner = config["dim_config"]["owner"]
        dq_check = NotNull(
                    project_id="test_project_id",
                    dataset_id="test_dataset_id",
                    table_id="test_table_id",
                    config=config['dim_config']['tests'][0]['config'],
                    dataset_owner=dataset_owner)
        _, generated_sql = dq_check.generate_test_sql()

        expected_sql = dedent("""WITH CTE AS (SELECT
                                COUNT(*) AS row_count
                                , segment 
                                FROM `test_project_id.test_dataset_id.test_table_id`
                                WHERE
                                submission_date = DATE("2020-01-13")
                                AND segment IS NULL 
                                GROUP BY 
                                segment  )

                                SELECT TO_JSON_STRING(CTE) as additional_information, "test_project_id" as project_id,
                                "test_dataset_id" as dataset_id,
                                "test_table_id" as table_id,
                                "not_null" as dq_check, 
                                "['akommasani@mozilla.com']" as dataset_owner,
                                "" as slack_alert,
                                CURRENT_DATE() as created_date
                                FROM CTE 
                                WHERE row_count >= 1""")
        assert expected_sql.replace(' ','').strip() == generated_sql.replace(' ','').strip()