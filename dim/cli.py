import click
import logging
from datetime import datetime

import yaml
import os
from dim.models.tests.not_null import NotNull
from dim.models.tests.uniqueness import Uniqueness
from dim.models.tests.custom_sql_metrics import CustomSqlMetrics
from dim.models.tests.table_row_count import TableRowCount

CONFIG_ROOT_PATH = "dim_checks"
TEST_CLASS_MAPPING = {"not_null": NotNull, "uniqueness": Uniqueness, "sql_metrics" : CustomSqlMetrics, "table_row_count" : TableRowCount}


def get_all_paths_yaml(name, config_root_path: str):
    result = []
    for root, dirs, files in os.walk(config_root_path):
        for file in files:
            if name in file:
                result.append(os.path.join(root, file))
    return result


def read_config(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config

logging.basicConfig(
    filename="Dim.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8",
    level=logging.INFO,
)


@click.group()
def cli():
    pass


@cli.command()
def run():
    name = '.yml'
    for config_path in get_all_paths_yaml(name, CONFIG_ROOT_PATH):
        config = read_config(config_path=config_path)
    # TODO: validate config, correct keys + types --add a function
        project_id, dataset_id, table_id = config_path.split("/")[1:-1]
        for config in config["dim_config"]:
            dataset_owner = config["owner"]
            for test in config["tests"]:
                test_type = test["type"]
                dq_check = TEST_CLASS_MAPPING[test_type](
                    project_id=project_id,
                    dataset_id=dataset_id,
                    table_id=table_id,
                    config=test["config"],
                    dataset_owner=dataset_owner)
                if test_type not in "sql_metrics" :
                     _, test_sql = dq_check.generate_test_sql()
                elif test["config"]["sql"]:
                    test_sql = test["config"]["sql"]
                dq_check.execute_test_sql(sql=test_sql)

@cli.command()
@click.argument("config_dir", required=True, type=click.Path(file_okay=False))
def validate_config(config_dir):
    logging.info(f"Validating config files in: {config_dir}")