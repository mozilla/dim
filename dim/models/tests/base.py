import jinja2
from pathlib import Path
from os import path
import logging
from google.cloud import bigquery


# TODO: these should go into some sort of utils module
def create_directory(path_to_create: Path) -> bool:
    logging.info("Creating directory: %s" % path_to_create)
    path_to_create.mkdir(parents=True)
    return True

def check_directory_exists(path_to_check: Path) -> bool:
    return path.exists(path_to_check)

def sql_to_file(target_file: Path, sql: str) -> bool:
    with open(target_file, "w+") as _file:
        _file.write(sql)

    return True

CREDS = "test_service_account.json"
GCP_PROJECT = "data-monitoring-dev"
GENERATED_SQL_FOLDER = "generated_sql"

class Base:
    TEMPLATES_LOC = "dim/models/tests/templates"
    TEMPLATE_FILE_EXTENSION = ".sql.jinja"

    def __init__(self, config: dict):
        self.config = config

    def generate_test_sql(self, test_type):
        generated_sql_folder = Path(GENERATED_SQL_FOLDER + "/" + self.config["project_id"]+"/"+ self.config["dataset_id"] +"/" + self.config["table_id"])
        check_directory_exists(generated_sql_folder) or create_directory(generated_sql_folder)

        templateLoader = jinja2.FileSystemLoader(searchpath=self.TEMPLATES_LOC)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(test_type + self.TEMPLATE_FILE_EXTENSION)

        target_file = generated_sql_folder.joinpath(f'{test_type}.sql')
        generated_sql = template.render(self.config)
        sql_to_file(target_file=target_file, sql=generated_sql)

        return target_file, generated_sql

    def execute_test_sql(self, sql):
        # TODO: extract authentication logic into separate module
        client = bigquery.Client(project=GCP_PROJECT)
        return client.query(sql).result()