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
    "table_row_count": getattr(table_row_count, "TableRowCount"), # noqa: F405
    "length_of_column": getattr(length_of_column, "LengthOfColumn"),   # noqa: F405
}


GCP_PROJECT = "data-monitoring-dev"
SOURCE_PROJECT = "data-monitoring-dev"

GENERATED_SQL_FOLDER = "generated_sql"

DESTINATION_PROJECT = "data-monitoring-dev"
DESTINATION_DATASET = "monitoring_derived"
DESTINATION_TABLE = "test_results"
