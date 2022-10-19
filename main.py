"""Generate the sql from metadata. """

from datetime import timedelta, datetime
import os
from traceback import print_exc

import yaml
from schema import Or, Optional, Schema, SchemaError

from dim.bigquery_client import BigQueryClient
from dim.models.dq_checks.custom_sql_metrics import CustomSqlMetrics
from dim.models.dq_checks.not_null import NotNull
from dim.models.dq_checks.table_row_count import TableRowCount
from dim.models.dq_checks.uniqueness import Uniqueness
from dim.slack import Slack
import dim.error as error
import logging

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
        AND table = '{table}'
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


def run(project, dataset, date_partition_parameter):
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
                        table,
                        test_type,
                        slack_handles,
                        date_partition_parameter,
                    )


def send_slack_alert(
    channel, project, dataset, table, test_type, slack_handles, date_partition_parameter
):
    slack = Slack()
    print(test_type)
    df = get_failed_dq_checks(project, dataset, table, test_type, date_partition_parameter)
    print(df)
    print(slack_handles)
    slack.format_and_publish_slack_message(df, channel, slack_handles=slack_handles)


def backfill(project,
    dataset,
    table,
    start_date,
    end_date):

    if (start_date > end_date ):
        raise error.NoStartDateException()

    for date in [
        start_date + timedelta(days=d) for d in range(0, (end_date - start_date).days + 1)
    ]:
        logging.info(f"Backfill started for the date {date}")

        # run(project, dataset, date)

        logging.info(f"Backfill completed for the date {date}")



expected_schema = Schema({
    "dim_config":[
        {
         "owner":{
            "email":list,
            Optional("slack_handle"):list
         },
        "tests":[
            {
              "type": Or("table_row_count", "not_null", "custom_sql_metric", "uniqueness"),
               "config":{
                   Optional("columns"):list,
                   Optional("sql"):str,
                  "threshold":str,
                  "slack_alert":str,
                   Optional("channel"): list
                    }
            }
                ]
        }
   ]
}
)

def validate_config():
    file =  CONFIG_ROOT_PATH + "/data-monitoring-dev/dummy/active_users_aggregates_v1/dim_checks.yml"
    config = read_config(file)

    try:
        expected_schema.validate(config)
        print("Configuration is valid.")
    except SchemaError as se:
        raise se

if __name__ == "__main__":
    # project = "data-monitoring-dev"
    # dataset = "dummy"
    # table ="active_users_aggregates_v1"
    # date_partition_parameter = "2022-01-13"
    # date_partition_parameter = datetime.strptime(
    #     date_partition_parameter, "%Y-%m-%d"
    # ).date()
    # start_date = "2021-01-10"
    # start_date = datetime.strptime(
    #     start_date, "%Y-%m-%d"
    # ).date()
    # end_date = "2021-01-12"
    # end_date = datetime.strptime(
    #     end_date, "%Y-%m-%d"
    # ).date()
    # # run(project, dataset, date_partition_parameter)
    # backfill(project, dataset, table, start_date, end_date)
    validate_config()
