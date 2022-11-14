import logging
import os

# from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List

import yaml
from google.cloud.bigquery.job import WriteDisposition
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table

import dim.const
from dim.bigquery_client import BigQueryClient


def create_bq_table_if_not_exist(bq_client, table):
    if not bq_client.bq_table_exists(table):
        bq_client.create_table(table)


def get_dim_processing_info_table():
    schema = [
        SchemaField(name="project_id", field_type="STRING"),
        SchemaField(name="dataset", field_type="STRING"),
        SchemaField(name="table", field_type="STRING"),
        SchemaField(name="dim_check_type", field_type="STRING"),
        SchemaField(name="date_partition", field_type="DATE"),
        SchemaField(name="run_id", field_type="STRING"),
        SchemaField(name="total_bytes_billed", field_type="INTEGER"),
        SchemaField(name="total_bytes_processed", field_type="INTEGER"),
    ]

    table = Table(
        dim.const.PROCESSING_INFO_TABLE,
        schema=schema,
    )

    bigquery = BigQueryClient(
        project_id=dim.const.DESTINATION_PROJECT,
        dataset=dim.const.DESTINATION_DATASET,
    )

    create_bq_table_if_not_exist(bigquery, table)

    return table


def get_muted_alerts_table():
    schema = [
        SchemaField(name="project_id", field_type="STRING"),
        SchemaField(name="dataset", field_type="STRING"),
        SchemaField(name="table", field_type="STRING"),
        SchemaField(name="date_partition", field_type="DATE"),
    ]

    return Table(
        dim.const.MUTED_ALERTS_TABLE,
        schema=schema,
    )


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
        FROM `{dim.const.MUTED_ALERTS_TABLE}`
        WHERE
            project_id = '{project_id}'
            AND dataset = '{dataset}'
            AND table = '{table}'
            AND DATE(date_partition) = DATE('{date}')
        """
    )

    bigquery = BigQueryClient(
        project_id=dim.const.DESTINATION_PROJECT,
        dataset=dim.const.DESTINATION_DATASET,
    )

    bq_table = get_muted_alerts_table()

    create_bq_table_if_not_exist(bigquery, bq_table)

    job = bigquery.fetch_results(sql)
    result_df = job.result().to_dataframe()

    return bool(result_df["count"].iloc[0])


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
    create_bq_table_if_not_exist(bigquery, str(bq_table))

    date_partition = date.date()

    insert_data = [
        {
            "project_id": project_id,
            "dataset": dataset,
            "table": table,
            "date_partition": date_partition,
        }
    ]

    result = bigquery.client.insert_rows(bq_table, insert_data)

    if not result:
        logging.info(
            "Alerts for %s:%s.%s for partition: %s have been muted."
            % (project_id, dataset, table, date_partition)
        )

    # TODO: else: something went wrong, log error message


def unmute_alerts_for_date(
    project_id: str,
    dataset: str,
    table: str,
    date: Any,
):
    logging.info(
        "Unmuting alerts for %s:%s.%s for date: %s"
        % (project_id, dataset, table, date)
    )

    bigquery = BigQueryClient(
        project_id=dim.const.DESTINATION_PROJECT,
        dataset=dim.const.DESTINATION_DATASET,
    )

    bq_table = get_muted_alerts_table()
    create_bq_table_if_not_exist(bigquery, bq_table)

    if not is_alert_muted(project_id, dataset, table, date):
        logging.info(
            "Alerts not muted for %s:%s.%s for date: %s. \
                Nothing needs to be done."
            % (project_id, dataset, table, date)
        )
        return

    date_partition = date.date()

    delete_statement = dedent(
        f"""
        SELECT
            *
        FROM `{str(bq_table)}`
        WHERE
            NOT (
                project_id = '{project_id}'
                AND dataset = '{dataset}'
                AND table = '{table}'
                AND date_partition = '{date_partition}'
            )
        """
    )

    result, _ = bigquery.execute(
        delete_statement,
        dataset=dim.const.DESTINATION_DATASET,
        destination_table=dim.const.MUTED_ALERTS_TABLE_NAME,
        write_disposition=WriteDisposition.WRITE_TRUNCATE,
        schema_update_options=None,
    )

    if not result:
        # TODO: else: something went wrong, log error message
        pass

    logging.info(
        "Alerts for %s:%s.%s for partition: %s has been unmuted."
        % (project_id, dataset, table, date_partition)
    )


# def create_directory(path_to_create: Path) -> bool:
#     logging.info("Creating directory: %s" % path_to_create)
#     result = path_to_create.mkdir(parents=True)
#     return True


# def check_directory_exists(path_to_check: Path) -> bool:
#     return os.path.exists(path_to_check)


# def sql_to_file(target_file: Path, sql: str) -> bool:
#     with open(target_file, "w+") as _file:
#         _file.write(sql)
#     return True


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
