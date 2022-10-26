import logging

from dim.models.dim_config import DimConfig
from dim.models.dq_checks.custom_sql_metrics import CustomSqlMetrics
from dim.models.dq_checks.not_null import NotNull
from dim.models.dq_checks.table_row_count import TableRowCount
from dim.models.dq_checks.uniqueness import Uniqueness
from dim.utils import get_all_paths_yaml, read_config

CONFIG_ROOT_PATH = "dim_checks"

TEST_CLASS_MAPPING = {
    "not_null": NotNull,
    "uniqueness": Uniqueness,
    "custom_sql_metric": CustomSqlMetrics,
    "table_row_count": TableRowCount,
}
SOURCE_PROJECT = "data-monitoring-dev"
DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"
INPUT_DATE_FORMAT = "%Y-%m-%d"

CONFIG_EXTENSION = ".yaml"


def run_check(project, dataset, table, date_partition_parameter):
    logging.info(
        "Running data checks on %s:%s.%s for date: %s"
        % (project, dataset, table, date_partition_parameter)
    )

    config_paths = (
        CONFIG_ROOT_PATH + "/" + project + "/" + dataset + "/" + table
    )
    for config_path in get_all_paths_yaml(CONFIG_EXTENSION, config_paths):
        config = read_config(config_path=config_path)
        project, dataset, table = config_path.split("/")[1:-1]

        for config in config["dim_config"]:
            dim_config = DimConfig(**config)

            dataset_owner = dim_config.owner

            for dim_test in config["dim_tests"]:
                test_type = dim_test["type"]
                logging.info(dim_test["options"])

                dq_check = TEST_CLASS_MAPPING[test_type](
                    project=project,
                    dataset=dataset,
                    table=table,
                    config=dim_test["options"],
                    dataset_owner=dataset_owner["email"],
                    date_partition_parameter=date_partition_parameter,
                )

                _, test_sql = dq_check.generate_test_sql()

                # dq_check.execute_test_sql(sql=test_sql)
                logging.info(f"Running DQ check - {test_type}")

                is_slack_enabled = dim_test["options"]["slack_alert"].lower()
                logging.info(f"Slack notification has been {is_slack_enabled}")

                if is_slack_enabled == "enabled":
                    slack_handles = dataset_owner["slack_handle"]
                    # channel = dim_test["options"]["channel"]
                    #         send_slack_alert(
                    #             channel,q
                    #             project,
                    #             dataset,
                    #             table,
                    #             test_type,
                    #             slack_handles,
                    #             date_partition_parameter,
                    #         )
                    logging.info(f"Slack handle {slack_handles} ")

    logging.info(
        "Finished running data checks on %s:%s.%s for date: %s"
        % (project, dataset, table, date_partition_parameter)
    )
