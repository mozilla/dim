"""Generate the sql from metadata. """

import yaml
import os
from models.tests.not_null import NotNull
from models.tests.uniqueness import Uniqueness
from models.tests.custom_sql_metrics import CustomSqlMetrics
from models.tests.table_row_count import TableRowCount

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


def main():
    name = '.yml'
    for config_path in get_all_paths_yaml(name, CONFIG_ROOT_PATH):
        config = read_config(config_path=config_path)
    # TODO: validate config, correct keys + types --add a function
        project_id, dataset_id, table_id = config_path.split("/")[1:-1]
        for config in config["dim_config"]:
            for test in config["tests"]:
                test_type = test["type"]
                print(test_type)
                dq_check = TEST_CLASS_MAPPING[test_type](
                    project_id=project_id,
                    dataset_id=dataset_id,
                    table_id=table_id,
                    config=test["config"])
                if test_type not in "sql_metrics" :
                     _, test_sql = dq_check.generate_test_sql()
                elif test["config"]["sql"]:
                    test_sql = test["config"]["sql"]
                dq_check.execute_test_sql(sql=test_sql)


if __name__ == "__main__":
    main()
