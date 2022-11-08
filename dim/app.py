import json
import logging
from datetime import datetime
from textwrap import dedent
from uuid import uuid4

import attr
from tabulate import tabulate

from dim.bigquery_client import BigQueryClient
from dim.const import (
    CONFIG_EXTENSION,
    CONFIG_ROOT_PATH,
    DESTINATION_DATASET,
    DESTINATION_PROJECT,
    DESTINATION_TABLE,
    TEST_CLASS_MAPPING,
)
from dim.models.dim_config import DimConfig
from dim.slack import send_slack_alert
from dim.utils import get_all_paths_yaml, is_alert_muted, read_config

# import pandas as pd


def retrieve_failed_dim_checks(project_id, dataset, table, run_uuid):
    sql = dedent(
        f"""
        SELECT
            CONCAT(project_id, '.', dataset, '.', table) AS dataset,
            dq_check,
            actual_run_date,
            date_partition,
            owner,
            additional_information,
            run_id,
        FROM `{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{DESTINATION_TABLE}`
        WHERE
            project_id = '{project_id}'
            AND dataset = '{dataset}'
            AND table = '{table}'
            AND run_id = '{run_uuid}'
            AND NOT passed
        """
    )

    bigquery = BigQueryClient(
        project_id=DESTINATION_PROJECT, dataset=DESTINATION_DATASET
    )

    job = bigquery.fetch_results(sql)

    return job.result().to_dataframe().to_dict("records")


def format_failed_check_results(results):
    formatted_results = tabulate(
        results,
        headers="keys",
        tablefmt="psql",
        stralign="center",
    )

    # TODO: this message can be formatted better
    return f"Dim tests failed:\n{formatted_results}"


def run_check(project_id: str, dataset: str, table: str, date: datetime):
    run_uuid = uuid4()

    logging.info(
        "Running data checks on %s:%s.%s for date: %s (run_id: %s)"
        % (project_id, dataset, table, date, run_uuid)
    )

    config_paths = (
        CONFIG_ROOT_PATH + "/" + project_id + "/" + dataset + "/" + table
    )

    # TODO: it would also be nice to track bytes process
    # or billed to get an idea how much running each test costs

    for config_path in get_all_paths_yaml(CONFIG_EXTENSION, config_paths):
        dim_config = DimConfig.from_dict(
            read_config(config_path=config_path)["dim_config"]
        )

        alert_muted = is_alert_muted(project_id, dataset, table, date)
        slack_alert_settings = dim_config.slack_alerts

        for dim_test in dim_config.dim_tests:
            test_type = dim_test.type

            logging.info(
                "Running %s check on %s:%s.%s for date: %s"
                % (test_type, project_id, dataset, table, date)
            )

            dim_check = TEST_CLASS_MAPPING[test_type](
                project_id=project_id,
                dataset=dataset,
                table=table,
            )

            query_params = {
                **attr.asdict(dim_test.params),
                "owner": json.dumps(attr.asdict(dim_config.owner)),
                "alert_enabled": slack_alert_settings.enabled,
                "alert_muted": alert_muted,
                "partition": date,
                "run_id": run_uuid,
            }
            _, test_sql = dim_check.generate_test_sql(query_params)
            dim_check.execute_test_sql(sql=test_sql)

            logging.info(
                "Finished running %s check on %s:%s.%s for date: %s"
                % (test_type, project_id, dataset, table, date)
            )

        logging.info(
            "Retrieving failed results for %s:%s.%s for date: %s (run_id: %s)"
            % (project_id, dataset, table, date, run_uuid)
        )
        failed_dim_checks = retrieve_failed_dim_checks(
            project_id, dataset, table, run_uuid
        )

        if (
            failed_dim_checks
            and slack_alert_settings.enabled
            and not alert_muted
        ):
            logging.info(
                "Sending out an alert for %s:%s.%s for date: %s"
                % (project_id, dataset, table, date)
            )

            send_slack_alert(
                channels=slack_alert_settings.notify.channels,
                info=format_failed_check_results(failed_dim_checks),
            )

        else:
            logging.info(
                "Alerts are muted or disabled for %s:%s.%s for date: %s"
                % (project_id, dataset, table, date)
            )

    logging.info(
        "Test results have been stored in %s:%s.%s"
        % (DESTINATION_PROJECT, DESTINATION_DATASET, DESTINATION_TABLE)
    )

    logging.info(
        "Finished running data checks on %s:%s.%s for date: %s (run_id: %s)"
        % (project_id, dataset, table, date, run_uuid)
    )
