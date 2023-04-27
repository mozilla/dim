import json
import logging
import os
from textwrap import dedent
from typing import Any, Dict, List

from slack_sdk import WebClient


def format_slack_notification(
    results: List[Dict[Any, Any]], config_path: str, notify_channel: bool
) -> List[Dict[str, Any]]:
    """
    Formats dim results into a format supported by slack client chat.postMessage method.
    More info about the slack API here: https://api.slack.com/methods/chat.postMessage
    """

    dataset = results[0]["dataset"]
    date_partition = results[0]["date_partition"]
    run_id = results[0]["run_id"]
    owner = json.loads(results[0]["owner"]).get("slack")
    run_status = (
        ":large_green_circle: Passed"
        if bool([result for result in results if result["passed"]])
        else ":red_circle: Failed"
    )
    dim_config_link = f"https://github.com/mozilla/dim/tree/main/{config_path}"

    formatted_section_template = dedent(
        """
        *DIM check*: `{check_type}`
        *DIM check status*: {check_status}
        *DIM check title*: {check_title}
        *DIM check description*: {check_description}
        *DIM check result*: {check_result} | {check_context}
        *DIM check BQ job*: https://console.cloud.google.com/bigquery?project=data-monitoring-dev&j=bq:US:{bq_job_id}&page=queryresults  # noqa: E501
        ----------
        """.replace(
            "  # noqa: E501", ""
        )  # TODO: facepalm...
    )

    formatted_check_sections = [
        formatted_section_template.format(
            check_status=":large_green_circle: `Passed`"
            if dim_check["passed"]
            else ":red_circle: `Failed`",
            check_type=dim_check["dim_check_type"],
            check_title=dim_check["dim_check_title"],
            check_description=dim_check["dim_check_description"],
            bq_job_id=dim_check["bq_job_id"],
            check_result=dim_check["query_results"],
            check_context=dim_check["dim_check_context"],
        )
        for dim_check in results
    ]

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": dedent(
                    f"""\
                    ==================================================================
                    DIM CHECK NOTIFICATION - Overall status: {run_status}
                    ==================================================================
                    *Table*: `{dataset}`
                    *Date partition*: `{date_partition}`
                    *Owner*: <@{owner}> {"(cc: <!channel>)" if notify_channel else ""}
                    ----------
                    """
                ),
            },
        },
        # individual check results
        *[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": check_section,
                },
            }
            for check_section in formatted_check_sections
        ],
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": dedent(
                    f"""\
                    *DIM run id*: `{run_id}`
                    *DIM config*: {dim_config_link}
                    ==================================================================
                    """
                ),
            },
        },
    ]

    return blocks


def send_slack_alert(
    channels: List[str],
    message: List[Dict[str, Any]],
) -> None:
    # TODO: perhaps we should check 'SLACK_BOT_TOKEN' is set
    # before executing the tests if slack alerting enabled
    token = os.environ["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=token)

    logging.info("Sending out alerts to %s" % channels)

    for channel in channels:
        slack_client.chat_postMessage(
            channel=channel,
            text="\n".join([section["text"]["text"] for section in message]),
            blocks=message,
            link_names=True,
            unfurl_links=False,
            unfurl_media=False,
            icon_emoji=":robot_face:",
        )
