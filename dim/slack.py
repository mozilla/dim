import logging
import os
from typing import Any, Dict, List

from slack_sdk import WebClient

# from tabulate import tabulate

# def format_and_publish_slack_message(channels):
# if pd.to_numeric(data.shape[0]) > 0:
# from tabulate import tabulate
# df_tab = tabulate(
#     [list(row) for row in data.values],
#     headers=list(data.columns),
#     tablefmt="grid",
#     stralign="center",
# )


def send_slack_alert(
    channels: List[str],
    info: Dict[Any, Any],
):
    # TODO: perhaps we should check 'SLACK_BOT_TOKEN' is set
    # before executing the tests if slack alerting enabled
    token = os.environ["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=token)

    logging.info("Sending out alerts to %s" % channels)

    for channel in channels:
        slack_client.chat_postMessage(
            channel=channel,
            text=info,
            # as_user=True,
            # username="dim",
            # icon_emoji=":alert:",
        )
