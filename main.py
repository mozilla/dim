"""Generate the sql from metadata. """

import datetime
import os

import yaml

from dim.bigquery_client import BigQueryClient
from dim.models.dq_checks.custom_sql_metrics import CustomSqlMetrics
from dim.models.dq_checks.not_null import NotNull
from dim.models.dq_checks.table_row_count import TableRowCount
from dim.models.dq_checks.uniqueness import Uniqueness
from dim.slack import Slack

CONFIG_ROOT_PATH = "dim_checks"
TEST_CLASS_MAPPING = {
    "not_null": NotNull,
    "uniqueness": Uniqueness,
    "custom_sql_metric": CustomSqlMetrics,
    "table_row_count": TableRowCount,
}
DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"


def get_failed_dq_checks(project, dataset, table, test_type, date_partition_parameter):
    # TO-DO if tables are different for each dataset then loop through all of them
    sql = f"""
        SELECT additional_information, project, dataset, table, dq_check, dataset_owner, slack_alert, created_date 
        FROM `monitoring_derived.test_results`
        WHERE DATE(created_date) = CURRENT_DATE()
        AND project = '{project}'
        AND dataset = '{dataset}'
        AND dq_check = '{test_type}'
        AND table = '{table}
        """
    bigquery = BigQueryClient(project=DESTINATION_PROJECT, dataset=DESTINATION_DATASET)
    job = bigquery.fetch_results(sql)
    df = job.result().to_dataframe()
    print(df)
    return df


def get_all_paths_yaml(extension, config_root_path: str):
    result = []
    for root, dirs, files in os.walk(config_root_path):
        for file in files:
            if file.endswith(extension):
                result.append(os.path.join(root, file))
    return result


def read_config(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def main(project, dataset, date_partition_parameter):
    extension = ".yml"
    config_paths = CONFIG_ROOT_PATH + "/" + project + "/" + dataset
    for config_path in get_all_paths_yaml(extension, config_paths):
        config = read_config(config_path=config_path)
        project, dataset, table = config_path.split("/")[1:-1]
        for config in config["dim_config"]:
            # TODO: validate config, correct keys + types --add a function
            dataset_owner = config["owner"]["email"]
            for test in config["tests"]:
                test_type = test["type"]
                dq_check = TEST_CLASS_MAPPING[test_type](
                    project=project,
                    dataset=dataset,
                    table=table,
                    config=test["config"],
                    dataset_owner=dataset_owner,
                    date_partition_parameter=date_partition_parameter,
                )
                _, test_sql = dq_check.generate_test_sql()
                # dq_check.execute_test_sql(sql=test_sql)
                print(test["config"]["slack_alert"].lower())
                if test["config"]["slack_alert"].lower() == "enabled":
                    slack_handles = config["owner"]["slack_handle"]
                    channel = test["config"]["channel"]
                    send_slack_alert(
                        channel,
                        project,
                        dataset,
                        test_type,
                        slack_handles,
                        date_partition_parameter,
                    )


def send_slack_alert(
    channel, project, dataset, test_type, slack_handles, date_partition_parameter
):
    slack = Slack()
    print(test_type)
    get_failed_dq_checks(project, dataset, test_type, date_partition_parameter)
    df = get_failed_dq_checks(project, dataset, test_type, date_partition_parameter)
    print(df)
    print(slack_handles)
    slack.format_and_publish_slack_message(df, channel, slack_handles=slack_handles)


if __name__ == "__main__":
    project = "data-monitoring-dev"
    dataset = "dummy"
    date_partition_parameter = "2022-01-13"
    date_partition_parameter = datetime.datetime.strptime(
        date_partition_parameter, "%Y-%m-%d"
    ).date()
    main(project, dataset, date_partition_parameter)
