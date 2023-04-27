"""BigQuery handler."""
import logging
from textwrap import dedent
from typing import Any, Dict, Optional

import attr
from google.cloud import bigquery
from google.cloud.bigquery.job import WriteDisposition
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table
from google.cloud.exceptions import NotFound

from dim.const import (
    DESTINATION_DATASET,
    DESTINATION_PROJECT,
    MUTED_ALERTS_TABLE,
    MUTED_ALERTS_TABLE_NAME,
    PROCESSING_INFO_TABLE,
    RUN_HISTORY_TABLE,
)


@attr.s(auto_attribs=True, slots=True)
class BigQueryClient:
    """Handler for requests to BigQuery."""

    project_id: str
    dataset: str
    _client: Optional[bigquery.client.Client] = None

    @property
    def client(self) -> bigquery.client.Client:
        """Return BigQuery client instance."""
        self._client = self._client or bigquery.client.Client(self.project_id)
        return self._client

    def bq_table_exists(self, table_ref):
        try:
            self.client.get_table(table_ref)
        except NotFound:
            return False

        return True

    def create_table(self, table):
        logging.info("Creating new BQ table: %s" % table)
        return self.client.create_table(table)

    def fetch_results(self, sql):
        return self.client.query(sql)

    def execute(
        self,
        query: str,
        destination_table: Optional[str] = None,
        write_disposition: Optional[bigquery.job.WriteDisposition] = None,
        schema_update_options: Optional[bigquery.job.SchemaUpdateOption] = None,
        dataset: Optional[str] = None,
    ) -> None:
        """Execute a SQL query and applies the provided parameters."""
        bq_dataset = bigquery.dataset.DatasetReference.from_string(
            dataset if dataset else self.dataset,
            default_project=self.project_id,
        )
        kwargs: Dict[str, Any] = {
            "allow_large_results": True,
            "use_query_cache": False,
        }

        if destination_table:
            kwargs["destination"] = bq_dataset.table(destination_table)
            kwargs["write_disposition"] = bigquery.job.WriteDisposition.WRITE_APPEND
            kwargs["schema_update_options"] = bigquery.job.SchemaUpdateOption.ALLOW_FIELD_ADDITION

        if write_disposition:
            kwargs["write_disposition"] = write_disposition

        if not schema_update_options:
            del kwargs["schema_update_options"]

        config = bigquery.job.QueryJobConfig(default_dataset=bq_dataset, **kwargs)

        bq_query_job = self.client.query(query, config)
        result = bq_query_job.result()

        return result, {
            "total_bytes_billed": bq_query_job.total_bytes_billed,
            "total_bytes_processed": bq_query_job.total_bytes_processed,
            "job_id": bq_query_job.job_id,
        }


def retrieve_dim_checks(project_id, dataset, table, run_uuid, date_partition, failed_only=True):
    sql = dedent(
        f"""
        SELECT
            CONCAT(project_id, '.', dataset, '.', table) AS dataset,
            dim_check_type,
            dim_check_title,
            run_log.dim_check_description,
            FORMAT_DATE("%Y-%m-%d %H:%M:%S", run_log.actual_run_date) AS actual_run_date,  # noqa: E501
            date_partition,
            owner,
            query_results,
            dim_check_context,
            run_id,
            passed,
            bq_job_id,
        FROM `{RUN_HISTORY_TABLE}` AS run_log
        LEFT JOIN `data-monitoring-dev.dim.dim_run_processing_info_v1` AS processing
        USING(project_id, dataset, `table`, dim_check_type, dim_check_title, date_partition, run_id)
        WHERE
            date_partition = '{date_partition}'
            AND project_id = '{project_id}'
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


def create_bq_table_if_not_exist(bq_client, table):
    if not bq_client.bq_table_exists(table):
        bq_client.create_table(table)


def get_dim_processing_info_table():
    schema = [
        SchemaField(name="project_id", field_type="STRING"),
        SchemaField(name="dataset", field_type="STRING"),
        SchemaField(name="table", field_type="STRING"),
        SchemaField(name="dim_check_type", field_type="STRING"),
        SchemaField(name="dim_check_title", field_type="STRING"),
        SchemaField(name="dim_check_description", field_type="STRING"),
        SchemaField(name="date_partition", field_type="DATE"),
        SchemaField(name="run_id", field_type="STRING"),
        SchemaField(name="bq_job_id", field_type="STRING"),
        SchemaField(name="total_bytes_billed", field_type="INTEGER"),
        SchemaField(name="total_bytes_processed", field_type="INTEGER"),
    ]

    table = Table(
        PROCESSING_INFO_TABLE,
        schema=schema,
    )

    bigquery = BigQueryClient(
        project_id=DESTINATION_PROJECT,
        dataset=DESTINATION_DATASET,
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
        MUTED_ALERTS_TABLE,
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
        FROM `{MUTED_ALERTS_TABLE}`
        WHERE
            project_id = '{project_id}'
            AND dataset = '{dataset}'
            AND table = '{table}'
            AND DATE(date_partition) = DATE('{date}')
        """
    )

    bigquery = BigQueryClient(
        project_id=DESTINATION_PROJECT,
        dataset=DESTINATION_DATASET,
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
    logging.info("Muting alerts for %s:%s.%s for date: %s" % (project_id, dataset, table, date))

    bigquery = BigQueryClient(
        project_id=DESTINATION_PROJECT,
        dataset=DESTINATION_DATASET,
    )

    if is_alert_muted(project_id, dataset, table, date):
        logging.info(
            "Alerts already muted for %s:%s.%s for date: %s" % (project_id, dataset, table, date)
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
    logging.info("Unmuting alerts for %s:%s.%s for date: %s" % (project_id, dataset, table, date))

    bigquery = BigQueryClient(
        project_id=DESTINATION_PROJECT,
        dataset=DESTINATION_DATASET,
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
        dataset=DESTINATION_DATASET,
        destination_table=MUTED_ALERTS_TABLE_NAME,
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
