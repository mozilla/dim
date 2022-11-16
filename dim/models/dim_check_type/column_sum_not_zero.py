from typing import Any, Dict

from dim.models.dim_check_type.base import Base


class ColumnSumNotZero(Base):
    dim_check_type_NAME = "column_sum_not_zero"

    def __init__(
        self,
        project_id,
        dataset,
        table,
    ):
        super().__init__(project_id, dataset, table, self.dim_check_type_NAME)

    def generate_test_sql(
        self, *, params: Dict[Any, Any], extras: Dict[Any, Any]
    ) -> str:
        return super().generate_test_sql(params=params, extras=extras)

    def execute_test_sql(self, sql: str) -> Any:
        return super().execute_test_sql(sql=sql)
