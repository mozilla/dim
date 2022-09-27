from bigquery_client import BigQueryClient
from google.cloud import bigquery
from google import cloud
from jinja2 import Environment, FileSystemLoader
from utils import check_directory_exists, create_directory, sql_to_file


CREDS = "test_service_account.json"
GCP_PROJECT = "data-monitoring-dev"
GENERATED_SQL_FOLDER = "generated_sql"
DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "dummy"
DESTINATION_TABLE = "test_results"

class Base:
    TEMPLATES_LOC = "dim/models/tests/templates"
    TEMPLATE_FILE_EXTENSION = ".sql.jinja"


    def __init__(self, config: dict):
        self.config = config

    @property
    def bigquery(self):
        """Return the BigQuery client instance."""
        return BigQueryClient(project=self.config["project_id"], dataset=self.config["dataset_id"])


    def generate_test_sql(self, test_type):
        generated_sql_folder = Path(GENERATED_SQL_FOLDER + "/" + self.config["project_id"]+"/"+ self.config["dataset_id"] +"/" + self.config["table_id"])
        check_directory_exists(generated_sql_folder) or create_directory(generated_sql_folder)

        templateLoader = FileSystemLoader(searchpath=self.TEMPLATES_LOC)
        templateEnv = Environment(loader=templateLoader)
        template = templateEnv.get_template(test_type + self.TEMPLATE_FILE_EXTENSION)
        target_file = generated_sql_folder.joinpath(f'{test_type}.sql')
        generated_sql = template.render(self.config)
        sql_to_file(target_file=target_file, sql=generated_sql)
        return target_file, generated_sql

    def execute_test_sql(self, sql):
        destination_table = f"{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{DESTINATION_TABLE}"
        if self.bigquery.if_tbl_exists(table_ref=destination_table):
            try:
                self.bigquery.execute(
                    sql,
                    destination_table = f"{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{DESTINATION_TABLE}",
                    write_disposition=bigquery.job.WriteDisposition.WRITE_TRUNCATE,
                    dataset=f"{DESTINATION_DATASET}",
                )
            except cloud.exceptions.NotFound:
                print("Table not found")
        else:
            # TODO: get table name and schema from a config file
            schema=[
                    bigquery.SchemaField(name="count", field_type="INT64"),
                    bigquery.SchemaField(name="project_id", field_type="STRING"),
                    bigquery.SchemaField(name="dataset_id", field_type="STRING"),
                    bigquery.SchemaField(name="created_date", field_type="DATETIME"),
                    ]
            table = bigquery.Table(destination_table, schema=schema)
            # table = self.bigquery.create_table(table)  # Make an API request.
            # print(
            #         "Created table {}.{}.{}".format(table.project, table.dataset_id, table.table_id)
            #     )