# from pathlib import Path
from typing import Any, Dict

from jinja2 import BaseLoader, Environment, FileSystemLoader

import dim.const
from dim.bigquery_client import BigQueryClient


class Base:
    def __init__(
        self,
        project_id: str,
        dataset: str,
        table: str,
        dim_check_type: str,
    ):
        self.project_id = project_id
        self.dataset = dataset
        self.table = table
        self.dim_check_type = dim_check_type

    @property
    def bigquery(self):
        """Return the BigQuery client instance."""

        return BigQueryClient(
            project_id=dim.const.DESTINATION_PROJECT,
            dataset=dim.const.DESTINATION_DATASET,
        )

    def render_sql(self, params: Dict[str, Any]) -> str:
        """Render and return the SQL from a template."""

        templateLoader = FileSystemLoader(dim.const.TEMPLATES_LOC)
        templateEnv = Environment(loader=templateLoader)
        template = templateEnv.get_template(self.dim_check_type + dim.const.TEMPLATE_FILE_EXTENSION)

        sql = template.render({**params})

        return sql

    def generate_test_sql(self, *, params: Dict[Any, Any]):
        render_params = {
            "project_id": self.project_id,
            "dataset": self.dataset,
            "table": self.table,
            "dim_check_type": self.dim_check_type,
            "params": params,
        }

        generated_sql = self.render_sql(params=render_params)

        # re-rendering so that custom sql passed through can also support params
        return Environment(loader=BaseLoader).from_string(generated_sql).render(render_params)

    def execute_test_sql(self, sql):
        return self.bigquery.execute(
            sql,
            dataset=dim.const.DESTINATION_DATASET,
            destination_table=dim.const.RUN_HISTORY_TABLE_NAME,
        )
