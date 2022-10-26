import logging
import os
from pathlib import Path
import yaml
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
    project, dataset, table, test_type, date_partition_parameter, target_gcp_project, target_dataset,
):
    # TO-DO if tables are different
    # for each dataset then loop through all of them
    sql = f"""
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
    bigquery = BigQueryClient(
        project=target_gcp_project, dataset=target_dataset
    )
    job = bigquery.fetch_results(sql)
    df = job.result().to_dataframe()
    print(df)
    return df


def get_all_paths_yaml(extension, config_root_path: str):

    # TODO: this should live in utils.py
    result = []
    # logging.info(config_root_path)
    for root, dirs, files in os.walk(config_root_path):
        print(f"{files}")
        for file in files:
            print(f"{file}")
            if extension in file:
                result.append(os.path.join(root, file))
    if not result:
        logging.info("No config files found !")
        # TODO: raise exception?
    else:
        return result


def read_config(config_path: str):
    # TODO: move to utils.py
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config