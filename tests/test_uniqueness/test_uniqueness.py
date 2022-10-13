from dim.models.dq_checks.uniqueness import Uniqueness
from textwrap import dedent


def test_uniqueness_pass():
        """ """
        
        config = {'dim_config': {'owner': ['akommasani@mozilla.com'], 'tests': [{'type': 'uniqueness', 'config': {'columns':['segment', 'app_version'],'threshold': 'row_count >= 1'}}]}}
        dataset_owner = config["dim_config"]["owner"]
        dq_check = Uniqueness(
                    project_id="test_project_id",
                    dataset_id="test_dataset_id",
                    table_id="test_table_id",
                    config=config['dim_config']['tests'][0]['config'],
                    dataset_owner=dataset_owner)
        _, generated_sql = dq_check.generate_test_sql()

        expected_sql = dedent("""WITH CTE AS (SELECT
                                COUNT(*) AS row_count,   segment ,  app_version  
                                FROM `test_project_id.test_dataset_id.test_table_id`
                                WHERE
                                submission_date = DATE("2020-01-13")
                                GROUP BY 
                                segment ,  app_version  
                                HAVING COUNT(*) > 1)


                                SELECT TO_JSON_STRING(CTE) as additional_information, "test_project_id" as project_id,
                                "test_dataset_id" as dataset_id,
                                "test_table_id" as table_id,
                                "uniqueness" as dq_check, 
                                "['akommasani@mozilla.com']" as dataset_owner,
                                "" as slack_alert,
                                CURRENT_DATE() as created_date
                                FROM CTE 
                                WHERE row_count >= 1""")
        assert expected_sql.replace(' ','').strip() == generated_sql.replace(' ','').strip()
test_uniqueness_pass()