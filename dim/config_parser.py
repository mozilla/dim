import yaml
import os
from models.tests.not_null import NotNull
from models.tests.uniqueness import Uniqueness


CONFIG_ROOT_PATH = "dim_checks"
TEST_CLASS_MAPPING = {"not_null" : NotNull,"uniqueness" : Uniqueness}


def get_all_paths_yaml(name,config_root_path:str):
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
    for config_path in get_all_paths_yaml(name,CONFIG_ROOT_PATH):
        config = read_config(config_path=config_path)
    ## TODO: validate config, correct keys + types
        project_id, dataset_id, table_id = config_path.split("/")[1:-1]

        for config in config["dim_config"]:
            for test in config["tests"]:
                test_type = test["type"]
                dq_check = TEST_CLASS_MAPPING[test_type](project_id=project_id, dataset_id=dataset_id, table_id=table_id, config=test["config"])
                _, test_sql = dq_check.generate_test_sql()
                result = dq_check.execute_test_sql(sql=test_sql)
                row_count = sum([row.row_count for row in result])

                if row_count > 0:
                    print("test for " + test_type + " " + project_id + "."+ dataset_id + "." + table_id +" has " + str(row_count) +" values found!")
                else:
                    print("no null values found!")

if __name__ == "__main__":
    main()