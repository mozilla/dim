import os

import pandas as pd
from slack_sdk import WebClient
from tabulate import tabulate

from dim.utils import get_failed_dq_checks

DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"


class Slack:
    def __init__(self):
        pass

    def format_and_publish_slack_message(self, data, channels, slack_handles):
        token = os.environ["SLACK_BOT_TOKEN"]
        slack_client = WebClient(token=token)
        if pd.to_numeric(data.shape[0]) > 0:
            print(pd.to_numeric(data.shape[0]))
            df_tab = tabulate(
                [list(row) for row in data.values],
                headers=list(data.columns),
                tablefmt="grid",
                stralign="center",
            )
            slack_handle_string = list(
                map((lambda x: "<@" + x + ">"), slack_handles)
            )
            for channel in channels:
                slack_client.chat_postMessage(
                    channel=channel,  # TO-DO replace with dataset owner id
                    text=(
                        f":alert: {slack_handle_string} ",
                        "The following DQ check failed\n",
                    )
                    + df_tab,
                    as_user=True,
                )


def send_slack_alert(
    channel,
    project,
    dataset,
    table,
    test_type,
    slack_handles,
    date_partition_parameter,
):
    # TODO: this should live in slack.py
    slack = Slack()
    print(test_type)
    df = get_failed_dq_checks(
        project,
        dataset,
        table,
        test_type,
        date_partition_parameter,
        DESTINATION_PROJECT,
        DESTINATION_DATASET,
    )
    slack.format_and_publish_slack_message(
        df, channel, slack_handles=slack_handles
    )
