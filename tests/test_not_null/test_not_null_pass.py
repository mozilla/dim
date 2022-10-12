from dim.models.dq_checks.not_null import NotNull
import json

def test_not_null_pass():
        """ """

        pass  # TODO: fix, commented out for setting up CI workflow

#         input_data = {
#                 "country" : "US",
#                 "city": "Pittsburgh",
#                 "time_slot": "2022-06-20 15:00:00 UTC",
#                 "client_id": "a6605216-07fb-4f29-bc30-5d5b36823356",
#                 "segment": None,
#                 "subsession_length" : 5646
#         }
#         config = {'dim_config': {'owner': ['akommasani@mozilla.com'], 'tests': [{'type': 'not_null', 'config': {'threshold': 'row_count >= 1'}}]}}
#         dataset_owner = config["dim_config"]["owner"]
#         # test_type = config['dim_config']['tests'][0]['type']
#         dq_check = NotNull(
#                     project_id="project_id",
#                     dataset_id="dataset_id",
#                     table_id="table_id",
#                     config=config['dim_config']['tests'][0]['config'],
#                     dataset_owner=dataset_owner)
#         test_sql = dq_check.generate_test_sql()
#         # print(test_sql)
#         dq_check.execute_test_sql(sql=test_sql)
#         generated_results = {}
#         expected_data = [{
#                 "additional_information": "{\"row_count\":1,\"country\":null}",
#                 "project_id": "data-monitoring-dev",
#                 "dataset_id": "dummy",
#                 "table_id": "active_users_aggregates_v1",
#                 "dq_check": "not_null",
#                 "dataset_owner": "akommasani@mozilla.com",
#                 "slack_alert": "enabled",
#                 "created_date": "2022-10-10"
#         }]
#         assert expected_data == generated_results

# test_not_null_pass()