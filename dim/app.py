import json
import logging
from datetime import datetime
from textwrap import dedent
from uuid import uuid4

import attr

from dim.bigquery_client import BigQueryClient
from dim.const import CONFIG_EXTENSION, CONFIG_ROOT_PATH, TEST_CLASS_MAPPING
from dim.models.dim_config import DimConfig
from dim.slack import send_slack_alert
from dim.utils import get_all_paths_yaml, is_alert_muted, read_config

DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"


def run_check(project_id: str, dataset: str, table: str, date: datetime):
    run_uuid = uuid4()

    logging.info(
        "Running data checks on %s:%s.%s for date: %s (run_id: %s)"
        % (project_id, dataset, table, date, run_uuid)
    )

    config_paths = (
        CONFIG_ROOT_PATH + "/" + project_id + "/" + dataset + "/" + table
    )

    for config_path in get_all_paths_yaml(CONFIG_EXTENSION, config_paths):
        dim_config = DimConfig.from_dict(
            read_config(config_path=config_path)["dim_config"]
        )

        alert_muted = is_alert_muted(project_id, dataset, table, date)
        slack_alert_settings = dim_config.slack_alerts

        for dim_test in dim_config.dim_tests:
            dim_check = TEST_CLASS_MAPPING[dim_test.type](
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

            print(test_sql)

            dim_check.execute_test_sql(sql=test_sql)

        # TODO: extract into new function
        sql = dedent(
            f"""
            SELECT
                *
            FROM `monitoring_derived.test_results`
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

        failed_dim_checks = job.result().to_dataframe().to_dict("records")

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
                info=str(failed_dim_checks),
            )

        else:
            logging.info(
                "Alerts are muted or disabled for %s:%s.%s for date: %s"
                % (project_id, dataset, table, date)
            )

    logging.info(
        "Finished running data checks on %s:%s.%s for date: %s"
        % (project_id, dataset, table, date)
    )
