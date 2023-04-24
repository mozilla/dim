from typing import Any, Dict

from dim.models.dim_check_type.base import Base


class ColumnLength(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_description="Checking that the number of characters matches our expectations.",
    ):
        super().__init__(project_id, dataset, table, dim_check_type="column_length", dim_check_description=dim_check_description)

    # TODO: these two functions probably do not need to live here at all
    # they're defined in super() and this just calls super()
    def generate_test_sql(self, *, params: Dict[Any, Any]) -> str:
        return super().generate_test_sql(params=params)

    def execute_test_sql(self, sql: str) -> Any:
        return super().execute_test_sql(sql=sql)
