import logging
from datetime import datetime

from dim.const import CONFIG_EXTENSION, CONFIG_ROOT_PATH, TEST_CLASS_MAPPING
from dim.models.dim_config import DimConfig
from dim.slack import send_slack_alert
from dim.utils import get_all_paths_yaml, read_config


def run_check(project: str, dataset: str, table: str, date: datetime):
    logging.info(
        "Running data checks on %s:%s.%s for date: %s"
        % (project, dataset, table, date)
    )

    config_paths = (
        CONFIG_ROOT_PATH + "/" + project + "/" + dataset + "/" + table
    )
    for config_path in get_all_paths_yaml(CONFIG_EXTENSION, config_paths):
        project, dataset, table = config_path.split("/")[1:-1]

        dim_config = DimConfig(
            **read_config(config_path=config_path)["dim_config"]
        )
        # TODO: in future the rest of the code should
        # handle multiple owners and alerting people
        dataset_owner = dim_config.owner

        for dim_test in dim_config.dim_tests:
            test_type = dim_test["type"]

            dq_check = TEST_CLASS_MAPPING[test_type](
                project_id=project,
                dataset=dataset,
                table=table,
                dataset_owner=dataset_owner,
                config=dim_test["options"],
                date=date,
            )

            _, test_sql = dq_check.generate_test_sql()
            dq_check.execute_test_sql(sql=test_sql)

            if dim_test["options"]["enable_slack_alert"]:
                channel = dim_test["options"]["channel"]
                send_slack_alert(
                    channel,
                    project,
                    dataset,
                    table,
                    test_type,
                    dataset_owner[0]["slack_handle"],
                    date,
                )

    logging.info(
        "Finished running data checks on %s:%s.%s for date: %s"
        % (project, dataset, table, date)
    )
