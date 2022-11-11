import logging

from dim.models.dim_check_type import *  # noqa: F403, E501

CONFIG_ROOT_PATH = "dim_checks"
CONFIG_EXTENSION = ".yaml"
INPUT_DATE_FORMAT = "%Y-%m-%d"

LOGGING_LEVEL = logging.INFO

DIM_CHECK_CLASS_MAPPING = {
    "not_null": getattr(not_null, "NotNull"),  # noqa: F405
    "uniqueness": getattr(uniqueness, "Uniqueness"),  # noqa: F405
    "custom_sql_metric": getattr(
        custom_sql_metric, "CustomSqlMetric"  # noqa: F405
    ),
    "table_row_count": getattr(table_row_count, "TableRowCount"),  # noqa: F405
    "column_length": getattr(column_length, "ColumnLength"),  # noqa: F405
    "combined_column_uniqueness": getattr(
        combined_column_uniqueness, "CombinedColumnUniqueness"  # noqa: F405
    ),
    "value_in_set": getattr(value_in_set, "ValueInSet"),  # noqa: F405
    "compare_row_count_to_table": getattr(
        compare_row_count_to_table, "CompareRowCountToTable"  # noqa: F405
    ),
    "column_sum_not_zero": getattr(
        column_sum_not_zero, "ColumnSumNotZero"  # noqa: F405
    ),
}


GENERATED_SQL_FOLDER = "generated_sql"

GCP_PROJECT = "data-monitoring-dev"
SOURCE_PROJECT = "data-monitoring-dev"

DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "dim"

RUN_HISTORY_TABLE_NAME = "dim_run_history_v1"
RUN_HISTORY_TABLE = (
    f"{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{RUN_HISTORY_TABLE_NAME}"
)

PROCESSING_INFO_TABLE_NAME = "dim_run_processing_info_v1"
PROCESSING_INFO_TABLE = (
    f"{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{PROCESSING_INFO_TABLE_NAME}"
)

MUTED_ALERTS_TABLE_NAME = "dim_muted_alerts_v1"
MUTED_ALERTS_TABLE = (
    f"{DESTINATION_PROJECT}.{DESTINATION_DATASET}.{MUTED_ALERTS_TABLE_NAME}"
)

VALID_TIERS = ("tier_1", "tier_2", "tier_3")

TEMPLATES_LOC = "dim/models/dim_check_type/templates"
TEMPLATE_FILE_EXTENSION = ".sql.jinja"
