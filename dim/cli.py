import logging
import os

import click
import yaml

from datetime import timedelta
from dim.bigquery_client import BigQueryClient
from dim.models.dq_checks.custom_sql_metrics import CustomSqlMetrics
from dim.models.dq_checks.not_null import NotNull
from dim.models.dq_checks.table_row_count import TableRowCount
from dim.models.dq_checks.uniqueness import Uniqueness
from dim.slack import Slack
import dim.error as error

CONFIG_ROOT_PATH = "dim_checks"
TEST_CLASS_MAPPING = {
    "not_null": NotNull,
    "uniqueness": Uniqueness,
    "custom_sql_metric": CustomSqlMetrics,
    "table_row_count": TableRowCount,
}
DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"

logging.basicConfig(level=logging.INFO)


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
    logging.info(config_root_path)
    for root, dirs, files in os.walk(config_root_path):
        print(f"{files}")
        for file in files:
            print(f"{file}")
            if extension in file:
                result.append(os.path.join(root, file))
    if not result:
        logging.info(f"No config files found !")
    else:
        return result

def read_config(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

def send_slack_alert(
    channel, project, dataset, table, test_type, slack_handles, date_partition_parameter
):
    slack = Slack()
    print(test_type)
    df = get_failed_dq_checks(
        project, dataset, table, test_type, date_partition_parameter
    )
    slack.format_and_publish_slack_message(df, channel, slack_handles=slack_handles)

@click.group()
def cli():
    pass


@cli.command()
@click.option("--project", default="data-monitoring-dev")
@click.option("--dataset")
@click.option("--table")
@click.option("--date_partition_parameter")
def run(project, dataset, table, date_partition_parameter):
    extension = ".yml"
    config_paths = CONFIG_ROOT_PATH + "/" + project + "/" + dataset + "/" + table
    for config_path in get_all_paths_yaml(extension, config_paths):
        config = read_config(config_path=config_path)
        project, dataset, table = config_path.split("/")[1:-1]
        logging.info(f"Starting the data checks - {project}, {dataset}, {table}")
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
                dq_check.execute_test_sql(sql=test_sql)
                logging.info(f"Running DQ check - {test_type}")
                is_slack_enabled = test["config"]["slack_alert"].lower()
                logging.info(f"Slack notification has been {is_slack_enabled}")
                if is_slack_enabled == "enabled":
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
                    logging.info(f"Users notified via {channel} ")


@cli.command()
@click.argument("config_dir", required=True, type=click.Path(file_okay=False))
def validate_config(config_dir):
    logging.info(f"Validating config files in: {config_dir}")


@cli.command()
@click.option("--project", default="data-monitoring-dev")
@click.option("--dataset")
@click.option("--table")
@click.option("--start_date")
@click.option("--end_date")
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

        run(project, dataset, table, date)

        logging.info(f"Backfill completed for the date {date}")