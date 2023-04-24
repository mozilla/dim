import json
import logging
from datetime import datetime
from textwrap import dedent
from uuid import uuid4
from enum import Enum

import attr
import jinja2

from dim.bigquery_client import BigQueryClient
from dim.const import (
    CONFIG_FILENAME,
    CONFIG_ROOT_PATH,
    DESTINATION_DATASET,
    DESTINATION_PROJECT,
    DIM_CHECK_CLASS_MAPPING,
    PROCESSING_INFO_TABLE,
    RUN_HISTORY_TABLE,
)
from dim.error import DimChecksFailed
from dim.models.dim_config import DimConfig
from dim.slack import send_slack_alert, format_slack_notification
from dim.utils import get_dim_processing_info_table, is_alert_muted, read_config


def retrieve_dim_checks(project_id, dataset, table, run_uuid, failed_only=True):
    sql = dedent(
        f"""
        SELECT
            CONCAT(project_id, '.', dataset, '.', table) AS dataset,
            dim_check_type,
            dim_check_description,
            FORMAT_DATE("%Y-%m-%d %H:%M:%S", actual_run_date) AS actual_run_date,  # noqa: E501
            date_partition,
            owner,
            query_results,
            dim_check_context,
            run_id,
            passed,
        FROM `{RUN_HISTORY_TABLE}`
        WHERE
            project_id = '{project_id}'
            AND dataset = '{dataset}'
            AND table = '{table}'
            AND run_id = '{run_uuid}'
            {"AND NOT passed" if failed_only else ""}
        """.replace(
            "  # noqa: E501", ""
        )
    )

    bigquery = BigQueryClient(project_id=DESTINATION_PROJECT, dataset=DESTINATION_DATASET)

    job = bigquery.fetch_results(sql)

    return job.result().to_dataframe()


def insert_dim_processing_info(insert_data):
    bigquery = BigQueryClient(project_id=DESTINATION_PROJECT, dataset=DESTINATION_DATASET)

    processing_table = get_dim_processing_info_table()

    result = bigquery.client.insert_rows(processing_table, insert_data)
    run_id = insert_data[0]["run_id"]

    if result:
        logging.error(
            "There has been a problem inserting processing \
                info into: %s for run_id: %s"
            % (str(processing_table), run_id)
        )
        logging.error(str(result))

    logging.info(
        "Processing info inserted into: %s for run_id: %s." % (PROCESSING_INFO_TABLE, run_id)
    )


def prepare_params(
    project_id,
    dataset,
    table,
    *,
    dim_config,
    alert_muted,
    check_params,
    run_uuid,
    date_partition,
):
    query_params = {
        **attr.asdict(check_params),
        "owner": json.dumps(attr.asdict(dim_config.owner)),
        "alert_enabled": dim_config.slack_alerts.enabled,
        "alert_muted": alert_muted,
        "partition": date_partition,
        "run_id": run_uuid,
        "tier": dim_config.tier,
        "partition_field": dim_config.partition_field,
    }

    if user_sql := query_params.get("sql"):
        templated_fields = {
            "project_id": project_id,
            "dataset": dataset,
            "table": table,
            "date_partition": date_partition,
        }

        user_sql_template = jinja2.Environment().from_string(user_sql)
        rendered_user_sql = user_sql_template.render(**templated_fields)
        query_params["sql"] = dedent(rendered_user_sql)

    return query_params


def run_check(
    project_id: str,
    dataset: str,
    table: str,
    date: datetime,
    fail_process_on_failure: bool = False,
):
    run_uuid = str(uuid4())
    date_partition = date.date()

    table_params = {
        "project_id": project_id,
        "dataset": dataset,
        "table": table,
    }
    table_param_values = table_params.values()

    logging.info(
        "Running data checks on %s:%s.%s for date_partition: %s (run_id: %s)"
        % (*table_param_values, date_partition, run_uuid)
    )

    config_path = f"{CONFIG_ROOT_PATH}/{project_id}/{dataset}/{table}/{CONFIG_FILENAME}"
    # TODO: add a check to make sure the config file exists

    dim_config = DimConfig.from_dict(read_config(config_path=config_path)["dim_config"])

    # TODO: fix the alert level setting
    notification_level = dim_config.slack_alerts.notification_level
    alert_muted = is_alert_muted(*table_param_values, date_partition)

    table_processing_info = list()

    # TODO: test execution could technically be taking place in parallel
    for dim_test in dim_config.dim_tests:
        test_type = dim_test.type
        test_description = dim_test.description

        logging.info(
            "Running %s check on %s:%s.%s for date_partition: %s"
            % (test_type, *table_param_values, date_partition)
        )

        dim_check = DIM_CHECK_CLASS_MAPPING[test_type](**table_params, dim_check_description=test_description)

        query_params = prepare_params(
            *table_params,
            dim_config=dim_config,
            alert_muted=alert_muted,
            check_params=dim_test.params,
            run_uuid=run_uuid,
            date_partition=date_partition,
        )

        test_sql = dim_check.generate_test_sql(
            params=query_params,
        )

        _, processing_info = dim_check.execute_test_sql(
            sql=test_sql.replace(
                "'[[dim_check_sql]]'",
                "'''"
                + test_sql.replace("\\", "\\\\").replace(
                    "'[[dim_check_sql]]' AS dim_check_sql,", ""
                )
                + "'''",
            )
        )

        table_processing_info.append(
            {
                **table_params,
                "date_partition": date_partition,
                "dim_check_type": test_type,
                "dim_check_description": test_description,
                "run_id": run_uuid,
                "total_bytes_billed": processing_info["total_bytes_billed"],
                "total_bytes_processed": processing_info["total_bytes_processed"],
            }
        )

        logging.info(
            "Finished running %s check on %s:%s.%s for date_partition: %s"
            % (test_type, *table_params.values(), date_partition)
        )

    insert_dim_processing_info(table_processing_info)
    logging.info("Test results have been stored in %s" % RUN_HISTORY_TABLE)

    logging.info(
        "Retrieving check results for %s:%s.%s for date_partition: %s (run_id: %s)"  # noqa: E501
        % (*table_param_values, date_partition, run_uuid)
    )

    errors_only = notification_level.upper() == "ERROR"
    dim_checks = retrieve_dim_checks(*table_param_values, run_uuid, failed_only=errors_only).to_dict("records")
    dim_checks_failed = bool([dim_check for dim_check in dim_checks if not dim_check["passed"]])

    # if notification_level >= NotificationLevel.ERROR and not dim_config.slack_alerts.enabled and not alert_muted:
    if dim_config.slack_alerts.enabled and not alert_muted and dim_checks:
        logging.info(
            "Sending out an alert for %s:%s.%s for date_partition: %s"
            % (*table_param_values, date_partition)
        )

        send_slack_alert(
            channels=dim_config.slack_alerts.notify.channels,
            message=format_slack_notification(dim_checks),
        )
    else:
        logging.info(
                "Alerts are muted or disabled for table: %s:%s.%s for date_partition: %s"  # noqa: E501
                % (*table_param_values, date_partition)
            )

    logging.info(
        "Finished running data checks on %s:%s.%s for date_partition: %s (run_id: %s)"  # noqa: E501
        % (*table_param_values, date_partition, run_uuid)
    )

    if dim_checks_failed and fail_process_on_failure:
        raise DimChecksFailed(
            "Some dim checks failed during the run. Please check run_id: %s inside dim_run_history table for more information."  # noqa: E501
            % run_uuid
        )
