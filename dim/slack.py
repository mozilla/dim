import os
from datetime import date

import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from tabulate import tabulate



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
            slack_handle_string = list(map((lambda x: "<@" + x + ">"), slack_handles))
            for channel in channels:
                slack_client.chat_postMessage(
                    channel=channel,  # TO-DO replace with dataset owner id
                    text=f":alert: {slack_handle_string} The following DQ check failed\n"
                    + df_tab,
                    as_user=True,
                )
