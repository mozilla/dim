import logging
import os
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List

import yaml
from pandas import DataFrame

from dim.bigquery_client import BigQueryClient


def create_directory(path_to_create: Path) -> bool:
    logging.info("Creating directory: %s" % path_to_create)
    path_to_create.mkdir(parents=True)
    return True


def check_directory_exists(path_to_check: Path) -> bool:
    return os.path.exists(path_to_check)


def sql_to_file(target_file: Path, sql: str) -> bool:
    with open(target_file, "w+") as _file:
        _file.write(sql)
    return True


def get_failed_dq_checks(
    project: str,
    dataset: str,
    table: str,
    test_type: str,
    date: str,
    target_gcp_project: str,
    target_dataset: str,
) -> DataFrame:
    # TO-DO if tables are different
    # for each dataset then loop through all of them
    sql = dedent(
        f"""
        SELECT
            additional_information,
            project,
            dataset,
            table,
            dq_check,
            dataset_owner,
            slack_alert,
            created_date,
        FROM `monitoring_derived.test_results`
        WHERE DATE(created_date) = CURRENT_DATE()
        AND project = '{project}'
        AND dataset = '{dataset}'
        AND dq_check = '{test_type}'
        AND table = '{table}'
        """
    )

    bigquery = BigQueryClient(
        project=target_gcp_project, dataset=target_dataset
    )
    job = bigquery.fetch_results(sql)

    return job.result().to_dataframe()


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
