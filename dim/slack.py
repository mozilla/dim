from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from tabulate import tabulate
import os
import pandas as pd
from google.cloud import bigquery

DESTINATION_PROJECT = "alekhya-test-1-322715"
class Slack:


    def __init__(self):
        pass


    def get_failed_dq_checks(self):
        bq_client = bigquery.Client(project=DESTINATION_PROJECT)
        # TO-DO if tables are different for each dataset then loop through all of them 
        sql_query = ("""
            SELECT additional_information, project_id, dataset_id, table_id, dq_check, dataset_owner, slack_alert, created_date 
            FROM `monitoring_derived.test_results`
            LIMIT 1
            """)
        df = bq_client.query(sql_query).to_dataframe()
        return df


    def format_and_publish_slack_message(self, data):
            token = os.environ["SLACK_BOT_TOKEN"]
            slack_client = WebClient(token=token)
            if pd.to_numeric(data.shape[0]) > 0:
                df_tab  = tabulate([list(row) for row in data.values], headers=list(data.columns), tablefmt="grid", stralign="center")
            else:
                df_tab = "No issue found"
            slack_client.chat_postMessage(
            channel = "#data-monitoring-mvp",        #TO-DO replace with dataset owner id
            text = ':alert: The following DQ check failed\n'
             + df_tab, 
            as_user = True
            )
