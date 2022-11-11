from typing import Any, Dict

from dim.models.dim_check_type.base import Base


class TableRowCount(Base):
    DQ_CHECK_NAME = "table_row_count"

    def __init__(
        self,
        project_id,
        dataset,
        table,
    ):
        super().__init__(project_id, dataset, table, self.DQ_CHECK_NAME)

    def generate_test_sql(
        self, *, params: Dict[Any, Any], extras: Dict[Any, Any]
    ) -> str:
        return super().generate_test_sql(params=params, extras=extras)

    def execute_test_sql(self, sql: str) -> Any:
        return super().execute_test_sql(sql=sql)
