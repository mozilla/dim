import logging
import os
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List

import yaml
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table
from pandas import DataFrame

import dim.const
from dim.bigquery_client import BigQueryClient


def create_directory(path_to_create: Path) -> bool:
    logging.info("Creating directory: %s" % path_to_create)
    path_to_create.mkdir(parents=True)
    return True


def check_directory_exists(path_to_check: Path) -> bool:
    return os.path.exists(path_to_check)


def sql_to_file(target_file: Path, sql: str) -> bool:
    with open(target_file, "w+") as _file:
        _file.write(sql)
    return True


def get_failed_dq_checks(
    project_id: str,
    dataset: str,
    table: str,
    test_type: str,
    date: str,
    target_gcp_project: str,
    target_dataset: str,
) -> DataFrame:
    # TO-DO if tables are different
    # for each dataset then loop through all of them
    sql = dedent(
        f"""
        SELECT
            additional_information,
            project,
            dataset,
            table,
            dq_check,
            dataset_owner,
            slack_alert,
            created_date,
        FROM `monitoring_derived.test_results`
        WHERE DATE(created_date) = CURRENT_DATE()
        AND project_id = '{project_id}'
        AND dataset = '{dataset}'
        AND dq_check = '{test_type}'
        AND table = '{table}'
        """
    )

    bigquery = BigQueryClient(
        project_id=dim.const.DESTINATION_PROJECT,
        dataset=dim.const.DESTINATION_DATASET,
    )
    job = bigquery.fetch_results(sql)

    return job.result().to_dataframe()


def get_muted_alerts_table():
    schema = [
        SchemaField(name="project_id", field_type="STRING"),
        SchemaField(name="dataset", field_type="STRING"),
        SchemaField(name="table", field_type="STRING"),
        SchemaField(name="partition_muted", field_type="DATE"),
    ]

    table = Table(
        f"""\
            {dim.const.DESTINATION_PROJECT}.{dim.const.DESTINATION_DATASET}.muted_alerts\
        """,
        schema=schema,
    )

    return table


def create_muted_alerts_table_if_not_exists(bq_client, table):
    if not bq_client.if_tbl_exists(table):
        bq_client.create_table(table)

    return True


def is_alert_muted(
    project_id: str,
    dataset: str,
    table: str,
    date: str,
) -> bool:
    sql = dedent(
        f"""
        SELECT
            COUNT(*) AS count,
        FROM `monitoring_derived.muted_alerts`
        WHERE
            project_id = '{project_id}'
            AND dataset = '{dataset}'
            AND table = '{table}'
            AND DATE(partition_muted) = DATE('{date}')
        """
    )

    bigquery = BigQueryClient(
        project_id=dim.const.DESTINATION_PROJECT,
        dataset=dim.const.DESTINATION_DATASET,
    )

    bq_table = get_muted_alerts_table()
    create_muted_alerts_table_if_not_exists(bigquery, str(bq_table))

    job = bigquery.fetch_results(sql)
    result_df = job.result().to_dataframe()

    return bool(result_df["count"].iloc[0])


def get_all_paths_yaml(extension: str, config_root_path: str) -> List[str]:

    result = []
    for root, _, files in os.walk(config_root_path):
        for file in files:
            if extension in file:
                result.append(os.path.join(root, file))

    if not result:
        logging.info("No config files found !")
        # TODO: raise exception?

    return result


def read_config(config_path: str) -> Dict[Any, Any]:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def mute_alerts_for_date(
    project_id: str,
    dataset: str,
    table: str,
    date: Any,
):
    logging.info(
        "Muting alerts for %s:%s.%s for date: %s"
        % (project_id, dataset, table, date)
    )

    bigquery = BigQueryClient(
        project_id=dim.const.DESTINATION_PROJECT,
        dataset=dim.const.DESTINATION_DATASET,
    )

    if is_alert_muted(project_id, dataset, table, date):
        logging.info(
            "Alerts already muted for %s:%s.%s for date: %s"
            % (project_id, dataset, table, date)
        )
        return

    bq_table = get_muted_alerts_table()
    create_muted_alerts_table_if_not_exists(bigquery, str(bq_table))

    insert_data = [
        {
            "project_id": project_id,
            "dataset": dataset,
            "table": table,
            "partition_muted": date.date(),
        }
    ]

    result = bigquery.client.insert_rows(bq_table, insert_data)

    if not result:
        pass
        # TODO: log alerts successfully muted
    # else: something went wrong, log error message
