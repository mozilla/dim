"""BigQuery handler."""
from typing import Any, Dict, Optional

import attr
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


@attr.s(auto_attribs=True, slots=True)
class BigQueryClient:
    """Handler for requests to BigQuery."""

    project: str
    dataset: str
    _client: Optional[bigquery.client.Client] = None

    @property
    def client(self) -> bigquery.client.Client:
        """Return BigQuery client instance."""
        self._client = self._client or bigquery.client.Client(self.project)
        return self._client

    def if_tbl_exists(self, table_ref):
        try:
            self.client.get_table(table_ref)
            return True
        except NotFound:
            return False

    def create_table(self, table):
        return self.client.create_table(table)

    def execute(
        self,
        query: str,
        destination_table: Optional[str] = None,
        write_disposition: Optional[bigquery.job.WriteDisposition] = None,
        dataset: Optional[str] = None,
    ) -> None:
        """Execute a SQL query and applies the provided parameters."""
        bq_dataset = bigquery.dataset.DatasetReference.from_string(
            dataset if dataset else self.dataset,
            default_project=self.project,
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

        config = bigquery.job.QueryJobConfig(default_dataset=bq_dataset, **kwargs)
        job = self.client.query(query, config)
        job.result()
