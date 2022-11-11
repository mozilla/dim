import json
import logging
from datetime import datetime
from textwrap import dedent
from uuid import uuid4

import attr
import jinja2
from tabulate import tabulate

from dim.bigquery_client import BigQueryClient
from dim.const import (
    CONFIG_EXTENSION,
    CONFIG_ROOT_PATH,
    DESTINATION_DATASET,
    DESTINATION_PROJECT,
    DIM_CHECK_CLASS_MAPPING,
    PROCESSING_INFO_TABLE,
    RUN_HISTORY_TABLE,
)
from dim.models.dim_config import DimConfig
from dim.slack import send_slack_alert
from dim.utils import (
    get_all_paths_yaml,
    get_dim_processing_info_table,
    is_alert_muted,
    read_config,
)

# import pandas as pd


def retrieve_failed_dim_checks(project_id, dataset, table, run_uuid):
    sql = dedent(
        f"""
        SELECT
            CONCAT(project_id, '.', dataset, '.', table) AS dataset,
            dim_check_type,
            actual_run_date,
            date_partition,
            owner,
            query_results,
            dim_check_context,
            run_id,
        FROM `{RUN_HISTORY_TABLE}`
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

    return job.result().to_dataframe()


def insert_dim_processing_info(insert_data):
    bigquery = BigQueryClient(
        project_id=DESTINATION_PROJECT, dataset=DESTINATION_DATASET
    )

    processing_table = get_dim_processing_info_table()
    print(processing_table)
    print(str(processing_table))

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
        "Processing info inserted into: %s for run_id: %s."
        % (PROCESSING_INFO_TABLE, run_id)
    )


def format_failed_check_results(results):
    dataset = results.iloc[0]["dataset"]
    date_partition = results.iloc[0]["date_partition"]
    run_id = results.iloc[0]["run_id"]
    owner = results.iloc[0]["owner"]

    results.drop(
        ["dataset", "date_partition", "run_id", "owner"], axis=1, inplace=True
    )

    fail_details_tbl = tabulate(
        results.to_dict("records"),
        headers="keys",
        tablefmt="psql",
        stralign="center",
    )

    formatted_results = dedent(
        f"""
        :alert: Dim checks failed:
        Table:     `{dataset}`
        Partition: `{date_partition}`
        Run id:    `{run_id}`
        Owner:     `{owner}`

        {fail_details_tbl}

        > For full context you can use the following query:
        ```
        SELECT * FROM `{RUN_HISTORY_TABLE}`
        WHERE
            run_id = "{run_id}"
            AND date_partition = DATE("{date_partition}")
        ```
        > And for full info around processing:
        ```
        SELECT * FROM `{PROCESSING_INFO_TABLE}`
        WHERE run_id = "{run_id}"
        AND date_partition = DATE("{date_partition}"
        ```
        """
    )

    return formatted_results


def run_check(project_id: str, dataset: str, table: str, date: datetime):
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

    config_paths = (
        CONFIG_ROOT_PATH + "/" + project_id + "/" + dataset + "/" + table
    )

    # TODO: this loop is unecessary
    for config_path in get_all_paths_yaml(CONFIG_EXTENSION, config_paths):
        dim_config = DimConfig.from_dict(
            read_config(config_path=config_path)["dim_config"]
        )

        alert_muted = is_alert_muted(*table_param_values, date_partition)
        slack_alert_settings = dim_config.slack_alerts

        table_processing_info = list()

        # TODO: test execution could technically be taking place in parallel
        for dim_test in dim_config.dim_tests:
            test_type = dim_test.type

            logging.info(
                "Running %s check on %s:%s.%s for date_partition: %s"
                % (test_type, *table_param_values, date_partition)
            )

            dim_check = DIM_CHECK_CLASS_MAPPING[test_type](**table_params)

            query_params = {
                **attr.asdict(dim_test.params),
                "owner": json.dumps(attr.asdict(dim_config.owner)),
                "alert_enabled": slack_alert_settings.enabled,
                "alert_muted": alert_muted,
                "partition": date_partition,
                "run_id": run_uuid,
            }

            if user_sql := query_params.get("sql"):
                templated_fields = {
                    **table_params,
                    "date_partition": date_partition,
                }

                user_sql_template = jinja2.Environment().from_string(user_sql)
                rendered_user_sql = user_sql_template.render(templated_fields)
                query_params["sql"] = dedent(rendered_user_sql)

            _, test_sql = dim_check.generate_test_sql(query_params)

            _, processing_info = dim_check.execute_test_sql(
                sql=test_sql.replace(
                    "'[[dim_check_sql]]'",
                    "'''"
                    + test_sql.replace(
                        "'[[dim_check_sql]]' AS dim_check_sql,", ""
                    )
                    + "'''",
                )
            )
            table_processing_info.append(
                {
                    **table_params,
                    "date_partition": date_partition,
                    "run_id": run_uuid,
                    "total_bytes_billed": processing_info[
                        "total_bytes_billed"
                    ],
                    "total_bytes_processed": processing_info[
                        "total_bytes_processed"
                    ],
                    "usd_cost_estimate": round(
                        (
                            (
                                (
                                    (
                                        (
                                            processing_info[
                                                "total_bytes_processed"
                                            ]
                                            / 1024
                                        )
                                        / 1024
                                    )
                                    / 1024
                                )
                                / 1024
                            )
                            * 5
                        ),
                        4,
                    ),
                }
            )

            logging.info(
                "Finished running %s check on %s:%s.%s for date_partition: %s"
                % (test_type, *table_params.values(), date_partition)
            )

        insert_dim_processing_info(table_processing_info)

        logging.info(
            "Retrieving failed results for %s:%s.%s for date_partition: %s (run_id: %s)"  # noqa: E501
            % (*table_param_values, date_partition, run_uuid)
        )
        failed_dim_checks = retrieve_failed_dim_checks(
            *table_param_values, run_uuid
        )

        if (
            failed_dim_checks.to_dict("records")
            and slack_alert_settings.enabled
            and not alert_muted
        ):
            logging.info(
                "Sending out an alert for %s:%s.%s for date_partition: %s"
                % (*table_param_values, date_partition)
            )

            send_slack_alert(
                channels=slack_alert_settings.notify.channels,
                info=format_failed_check_results(failed_dim_checks),
            )

        else:
            logging.info(
                "Alerts are muted or disabled for table: %s:%s.%s for date_partition: %s"  # noqa: E501
                % (*table_param_values, date_partition)
            )

    logging.info("Test results have been stored in %s" % RUN_HISTORY_TABLE)

    logging.info(
        "Finished running data checks on %s:%s.%s for date_partition: %s (run_id: %s)"  # noqa: E501
        % (*table_param_values, date_partition, run_uuid)
    )
