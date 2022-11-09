# from textwrap import dedent

# from dim.models.dim_config import DimConfig
# from dim.models.dim_check_type.not_null import NotNull


# def test_not_null_pass():
#     """ """

#     config = DimConfig.from_dict(
#         {
#             "owner": {"email": "akommasani@mozilla.com"},
#             "tier": "tier_3",
#             "slack_alerts": {
#                 "enabled": True,
#                 "notify": {
#                     "channels": ["mvp"]
#                 },
#             },
#             "dim_tests": [
#                 {
#                     "type": "not_null",
#                     "params": {
#                         "columns": ["segment"],
#                         "condition": "row_count >= 1",
#                     },
#                 }
#             ],
#         }
#     )
#     dim_check_type = NotNull(
#         project_id="test_project",
#         dataset="test_dataset",
#         table="test_table",
#     )
#     _, generated_sql = dim_check_type.generate_test_sql(config.dim_tests[0].params)  # noqa: E501

#     expected_sql = dedent(
#         """\
#         WITH CTE AS (
#             SELECT
#                 COUNT(*) AS row_count,
#                 segment,
#             FROM `test_project.test_dataset.test_table`
#             WHERE
#                 date_partition = DATE('2022-01-13')
#                 AND segment IS NULL
#             GROUP BY
#                 segment
#         )

#         SELECT
#             TO_JSON_STRING(CTE) AS query_results,
#             'test_project' AS project_id,
#             'test_dataset' AS dataset,
#             'test_table' AS table,
#             'not_null" AS dim_check_type,
#             '{"email": "akommasani@mozilla.com"}' AS dataset_owner,
#             'true' AS alerts_enabled,
#             CURRENT_DATETIME() AS actual_run_date
#         FROM CTE"""
#     )

#     assert expected_sql == generated_sql
