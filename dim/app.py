import logging
from datetime import datetime
from uuid import uuid4

from dim.bigquery_client import insert_dim_processing_info, is_alert_muted, retrieve_dim_checks
from dim.const import CONFIG_FILENAME, CONFIG_ROOT_PATH, DIM_CHECK_CLASS_MAPPING, RUN_HISTORY_TABLE
from dim.error import DimChecksFailed
from dim.models.dim_config import DimConfig
from dim.slack import format_slack_notification, send_slack_alert
from dim.utils import prepare_params, read_config


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
    # if config file does not exist:
    #   logging.info("No config files found !")
    #   return #TODO: maybe should raise an exception?

    dim_config = DimConfig.from_dict(read_config(config_path=config_path)["dim_config"])

    # TODO: fix the alert level setting
    notification_level = dim_config.slack_alerts.notification_level
    alert_muted = is_alert_muted(*table_param_values, date_partition)

    table_processing_info = list()

    # TODO: test execution could technically be taking place in parallel
    for dim_test in dim_config.dim_tests:
        test_type = dim_test.type
        test_title = dim_test.title
        test_description = dim_test.description

        logging.info(
            "Running %s check on %s:%s.%s for date_partition: %s"
            % (test_type, *table_param_values, date_partition)
        )

        dim_check = DIM_CHECK_CLASS_MAPPING[test_type](
            **table_params, dim_check_title=test_title, dim_check_description=test_description
        )

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

        # TODO: do we need to store the exact query executed inside this table?
        # could we just get a link to the executed job in bq and include the link instead?
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
                "dim_check_title": test_title,
                "dim_check_description": test_description,
                "run_id": run_uuid,
                "bq_job_id": processing_info["job_id"],
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
    dim_checks = retrieve_dim_checks(
        *table_param_values, run_uuid, date_partition, failed_only=errors_only
    ).to_dict("records")
    dim_checks_failed = bool([dim_check for dim_check in dim_checks if not dim_check["passed"]])

    if dim_config.slack_alerts.enabled and not alert_muted and dim_checks:
        logging.info(
            "Sending out an alert for %s:%s.%s for date_partition: %s"
            % (*table_param_values, date_partition)
        )

        send_slack_alert(
            channels=dim_config.slack_alerts.notify.channels,
            message=format_slack_notification(dim_checks, config_path),
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
