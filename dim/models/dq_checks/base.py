# import json
from pathlib import Path
from typing import Any, Dict

# from cattrs import unstructure
from jinja2 import Environment, FileSystemLoader

from dim.bigquery_client import BigQueryClient
from dim.utils import check_directory_exists, create_directory, sql_to_file

# TODO: fails due to circular import, needs resolution
# from dim.const import DESTINATION_PROJECT, \
# DESTINATION_DATASET, DESTINATION_TABLE

GENERATED_SQL_FOLDER = "generated_sql"

DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"
DESTINATION_TABLE = "test_results"

TEMPLATES_LOC = "dim/models/dq_checks/templates"
TEMPLATE_FILE_EXTENSION = ".sql.jinja"


class Base:
    def __init__(
        self,
        project_id: str,
        dataset: str,
        table: str,
        dq_check: str,
    ):
        self.project_id = project_id
        self.dataset = dataset
        self.table = table
        self.dq_check = dq_check

    @property
    def bigquery(self):
        """Return the BigQuery client instance."""

        return BigQueryClient(
            project_id=DESTINATION_PROJECT, dataset=DESTINATION_DATASET
        )

    def render_sql(self, render_kwargs: Dict[str, Any]):
        """Render and return the SQL from a template."""

        templateLoader = FileSystemLoader(TEMPLATES_LOC)
        templateEnv = Environment(loader=templateLoader)
        template = templateEnv.get_template(
            self.dq_check + TEMPLATE_FILE_EXTENSION
        )

        sql = template.render(**render_kwargs)

        return sql

    def generate_test_sql(self, params):
        generated_sql_folder = Path(
            GENERATED_SQL_FOLDER
            + "/"
            + self.project_id
            + "/"
            + self.dataset
            + "/"
            + self.table
        )

        check_directory_exists(generated_sql_folder) or create_directory(
            generated_sql_folder
        )

        target_file = generated_sql_folder.joinpath(f"{self.dq_check}.sql")
        generated_sql = self.render_sql(
            {
                "project_id": self.project_id,
                "dataset": self.dataset,
                "table": self.table,
                "dq_check": self.dq_check,
                "params": params,
            },
        )

        sql_to_file(target_file=target_file, sql=generated_sql)

        return target_file, generated_sql

    def execute_test_sql(self, sql):
        return self.bigquery.execute(
            sql,
            dataset=DESTINATION_DATASET,
            destination_table=DESTINATION_TABLE,
        )
