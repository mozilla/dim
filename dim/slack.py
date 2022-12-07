import logging
import os
from typing import Any, Dict, List

from slack_sdk import WebClient


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
