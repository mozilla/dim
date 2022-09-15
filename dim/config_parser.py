import yaml

from models.tests.not_null import NotNull

CONFIG_PATH = "dim/test_config.yml"


def read_config(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def main():
    configs = read_config(config_path=CONFIG_PATH)
    ## TODO: validate config, correct keys + types

    for config in configs["dim_config"]:
        dataset = config["dataset"]

        for test in config["tests"]:
            test_type = test["type"]
            test_name = dataset + "__" + test_type

            not_null = NotNull(name=test_name, dataset=dataset, config=test["config"])

    _, test_sql = not_null.generate_test_sql()
    result = not_null.execute_test_sql(sql=test_sql)
    rows_with_nulls = sum([row.row_count for row in result])

    if rows_with_nulls > 0:
        print("null values found!")
    else:
        print("no null values found!")

if __name__ == "__main__":
    main()