import os
from typing import List

import pandas as pd
from slack_sdk import WebClient
from tabulate import tabulate

from dim.utils import get_failed_dq_checks


def format_and_publish_slack_message(data, channels, slack_handles):
    # perhaps we should check 'SLACK_BOT_TOKEN' is set
    # before executing the tests if slack alerting enabled
    token = os.environ["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=token)

    if pd.to_numeric(data.shape[0]) > 0:
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
    channel: str,
    project: str,
    dataset: str,
    table: str,
    test_type: str,
    slack_handles: List[str],
    date: str,
):
    df = get_failed_dq_checks(
        project,
        dataset,
        table,
        test_type,
        date,
    )

    format_and_publish_slack_message(df, channel, slack_handles=slack_handles)
