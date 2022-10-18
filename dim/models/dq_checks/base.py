from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader

from dim.bigquery_client import BigQueryClient
from dim.utils import check_directory_exists, create_directory, sql_to_file
import logging

# CREDS = "test_servicemonitoring_account.json"
GCP_PROJECT = "data-monitoring-dev"
GENERATED_SQL_FOLDER = "generated_sql"
DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"
DESTINATION_TABLE = "test_results"

logging.basicConfig(level=logging.INFO)


class Base:
    TEMPLATES_LOC = "dim/models/dq_checks/templates"
    TEMPLATE_FILE_EXTENSION = ".sql.jinja"

    def __init__(self, config: dict):
        self.config = config

    @property
    def bigquery(self):
        """Return the BigQuery client instance."""
        return BigQueryClient(
            project=DESTINATION_PROJECT, dataset=DESTINATION_DATASET
        )

    def render_sql(self, dq_check: str, render_kwargs: Dict[str, Any]):
        """Render and return the SQL from a template."""
        templateLoader = FileSystemLoader(self.TEMPLATES_LOC)
        templateEnv = Environment(loader=templateLoader)
        template = templateEnv.get_template(
            dq_check + self.TEMPLATE_FILE_EXTENSION
        )
        sql = template.render(**render_kwargs)
        return sql

    def generate_test_sql(self, dq_check):
        generated_sql_folder = Path(
            GENERATED_SQL_FOLDER
            + "/"
            + self.config["project"]
            + "/"
            + self.config["dataset"]
            + "/"
            + self.config["table"]
        )
        check_directory_exists(generated_sql_folder) or create_directory(
            generated_sql_folder
        )
        target_file = generated_sql_folder.joinpath(f"{dq_check}.sql")
        generated_sql = self.render_sql(dq_check, self.config)
        sql_to_file(target_file=target_file, sql=generated_sql)
        return target_file, generated_sql

    def execute_test_sql(self, sql):
        logging.info(sql)
        logging.info(dir(self.bigquery))
        self.bigquery.execute(
            sql,
            destination_table=DESTINATION_TABLE,  # the tables can be different for each dataset depending on the size of dataset  # noqa: E501
            dataset=f"{DESTINATION_DATASET}",
        )
