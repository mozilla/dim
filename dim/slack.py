import json
import logging
import os
from textwrap import dedent
from typing import Any, Dict, List

from slack_sdk import WebClient


def format_slack_notification(results: List[Dict[Any, Any]]) -> str:
    dataset = results[0]["dataset"]
    date_partition = results[0]["date_partition"]
    run_id = results[0]["run_id"]
    owner = json.loads(results[0]["owner"]).get("slack")
    run_status = (
        ":large_green_circle: Passed"
        if bool([result for result in results if result["passed"]])
        else ":red_circle: Failed"
    )

    check_section_template = """
        *DIM check*: `{check_type}`
        *DIM check status*: {check_status}
        *DIM check description*: {check_description}
        *DIM check result*: {check_result} | {check_context}
        """

    check_sections = "\n---".join(
        [
            check_section_template.format(
                check_status=":large_green_circle: `Passed`"
                if dim_check["passed"]
                else ":red_circle: `Failed`",
                check_type=dim_check["dim_check_type"],
                check_name=dim_check["dim_check_title"],
                check_description=dim_check["dim_check_description"],
                check_result=dim_check["query_results"],
                check_context=dim_check["dim_check_context"],
            )
            for dim_check in results
        ]
    )

    formatted_message = dedent(
        f"""
        ======================================================================
        DIM CHECK NOTIFICATION - Overall status: {run_status}
        ======================================================================
        *Table*: `{dataset}`
        *Date partition*: `{date_partition}`
        *Owner*: <@{owner}>
        ----------
        {check_sections}
        ----------
        *Run ID*: `{run_id}`
        ======================================================================
        """
    )

    return formatted_message


def send_slack_alert(
    channels: List[str],
    message: str,
) -> None:
    # TODO: perhaps we should check 'SLACK_BOT_TOKEN' is set
    # before executing the tests if slack alerting enabled
    token = os.environ["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=token)

    logging.info("Sending out alerts to %s" % channels)

    for channel in channels:
        slack_client.chat_postMessage(
            channel=channel,
            text=message,
            #   blocks=[
            #     {
            #         "type": "section",
            #         "text": {
            #             "type": "mrkdwn",
            #             "text": "Danny Torrence left the following review for your property:"
            #         }
            #     },
            #     {
            #         "type": "section",
            #         "text": {
            #             "type": "mrkdwn",
            #             "text": "<https://example.com|Overlook Hotel> \n :star: \n Doors had too many axe holes, guest in room " +  # noqa: E501
            #                 "237 was far too rowdy, whole place felt stuck in the 1920s."
            #         },
            #         "accessory": {
            #             "type": "image",
            #             "image_url": "https://images.pexels.com/photos/750319/pexels-photo-750319.jpeg",  # noqa: E501
            #             "alt_text": "Haunted hotel image"
            #         }
            #     },
            #     {
            #         "type": "section",
            #         "fields": [
            #             {
            #                 "type": "mrkdwn",
            #                 "text": "*Average Rating*\n1.0"
            #             }
            #         ]
            #     }
            # ]
            # as_user=True,
            # username="dim",
            # icon_emoji=":`alert:",
        )
