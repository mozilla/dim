import logging
from datetime import timedelta

import click

from dim.models.dim_config import DimConfig
from dim.models.dq_checks.custom_sql_metrics import CustomSqlMetrics
from dim.models.dq_checks.not_null import NotNull
from dim.models.dq_checks.table_row_count import TableRowCount
from dim.models.dq_checks.uniqueness import Uniqueness
from dim.slack import Slack, send_slack_alert
from dim.utils import get_all_paths_yaml, read_config
from dim.error import DateRangeException

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


logging.basicConfig(level=logging.INFO)


def run_check(project, dataset, table, date_partition_parameter):
    logging.info("Running data checks on %s:%s.%s for date: %s" % (project, dataset, table, date_partition_parameter))

    # TODO: majority of this logic should be moved to a separate module
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
                    channel = dim_test["options"]["channel"]
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

    logging.info("Finished running data checks on %s:%s.%s for date: %s" % (project, dataset, table, date_partition_parameter))


def validate_date_range(start_date, end_date):
    if start_date > end_date:
        raise DateRangeException("Start date appears to be more recent than end date.")

    return start_date, end_date


@click.group()
def cli():
    pass

@cli.command()
@click.option("--project", required=False, type=str, default=SOURCE_PROJECT)
@click.option("--dataset", required=True, type=str)
@click.option("--table", required=True, type=str)  # required for now until we add support for grabbing all configs in a dataset
@click.option("--date_partition_parameter", required=True, type=click.DateTime(formats=[INPUT_DATE_FORMAT]))  # rename date_partition_parameter to something shorter, required until we add support for full tables
def run(project: str, dataset: str, table: str, date_partition_parameter: str):
    run_check(project, dataset, table, date_partition_parameter)


@cli.command()
@click.argument("config_dir", required=True, type=click.Path(file_okay=False))
def validate_config(config_dir):
    # TODO: needs implemented
    logging.info(f"Validating config files in: {config_dir}")


@cli.command()
@click.option("--project", required=False, type=str, default=SOURCE_PROJECT)
@click.option("--dataset", required=True, type=str)
@click.option("--table", required=True, type=str)  # required for now until we add support for grabbing all configs in a dataset
@click.option("--start_date", required=True, type=click.DateTime(formats=[INPUT_DATE_FORMAT]))
@click.option("--end_date", required=True, type=click.DateTime(formats=[INPUT_DATE_FORMAT]))
def backfill(project, dataset, table, start_date, end_date):
    """
    Cmd to trigger tests execution for the specified table
    for the specified date range.
    """

    validate_date_range(start_date, end_date)

    logging.info("Running dim backfill checks on %s:%s.%s for date range: %s - %s" % (project, dataset, table, start_date, end_date))

    date = start_date
    while date <= end_date:
        run_check(project, dataset, table, date)
        date += timedelta(days=1)

    logging.info("Dim backfill completed for %s:%s.%s for date range: %s - %s" % (project, dataset, table, start_date, end_date))
