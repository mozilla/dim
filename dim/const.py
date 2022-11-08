import logging

from dim.models.dq_checks import *  # noqa: F403

CONFIG_ROOT_PATH = "dim_checks"
CONFIG_EXTENSION = ".yaml"
INPUT_DATE_FORMAT = "%Y-%m-%d"

LOGGING_LEVEL = logging.INFO

TEST_CLASS_MAPPING = {
    "not_null": getattr(not_null, "NotNull"),  # noqa: F405
    "uniqueness": getattr(uniqueness, "Uniqueness"),  # noqa: F405
    "custom_sql_metric": getattr(
        custom_sql_metric, "CustomSqlMetric"  # noqa: F405
    ),
    "table_row_count": getattr(table_row_count, "TableRowCount"),  # noqa: F405
    "column_length": getattr(column_length, "ColumnLength"),  # noqa: F405
    "value_in_set": getattr(value_in_set, "ValueInSet"),  # noqa: F405
}


GENERATED_SQL_FOLDER = "generated_sql"

GCP_PROJECT = "data-monitoring-dev"
SOURCE_PROJECT = "data-monitoring-dev"

DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"
DESTINATION_TABLE = "dim_run_history_v1"

VALID_TIERS = ("tier_1", "tier_2", "tier_3")

MUTED_ALERTS_TABLE_NAME = "muted_alerts_v1"
MUTED_ALERTS_TABLE = (
    f"{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{MUTED_ALERTS_TABLE_NAME}"
)

TEMPLATES_LOC = "dim/models/dq_checks/templates"
TEMPLATE_FILE_EXTENSION = ".sql.jinja"
