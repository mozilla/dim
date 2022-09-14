import yaml
from google.cloud import bigquery

from models.tests.not_null import NotNull

CONFIG_PATH = "dim/test_config.yml"

def read_config(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def main():
    configs = read_config(config_path=CONFIG_PATH)

    for config in configs["dim_config"]:
        dataset = config["dataset"]

        for test in config["tests"]:
            test_type = test["type"]
            test_name = dataset + "__" + test_type

            not_null = NotNull(name=test_name, dataset=dataset, config=test["config"])
            test_sql = not_null.generate_test_sql()

    creds = "test_service_account.json"
    gcp_project = "data-monitoring-dev"

    client = bigquery.Client.from_service_account_json(json_credentials_path=creds, project=gcp_project)

    result = client.query(test_sql).result()
    rows_with_nulls = sum([row.row_count for row in result])

    if rows_with_nulls > 0:
        print("null values found!")
    else:
        print("no null values found!")

if __name__ == "__main__":
    main()