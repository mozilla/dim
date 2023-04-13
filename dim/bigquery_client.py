"""BigQuery handler."""
import logging
from typing import Any, Dict, Optional

import attr
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


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
        }
