from typing import Any, Dict

from dim.models.dim_check_type.base import Base


class ColumnLength(Base):
    # TODO: could move this directly into the init() call
    dim_check_type_NAME = "column_length"

    def __init__(
        self,
        project_id,
        dataset,
        table,
    ):
        super().__init__(project_id, dataset, table, self.dim_check_type_NAME)

    # TODO: these two functions probably do not need to live here at all
    # they're defined in super() and this just calls super()
    def generate_test_sql(self, *, params: Dict[Any, Any]) -> str:
        return super().generate_test_sql(params=params)

    def execute_test_sql(self, sql: str) -> Any:
        return super().execute_test_sql(sql=sql)
