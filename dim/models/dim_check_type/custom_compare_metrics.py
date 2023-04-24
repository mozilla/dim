from dim.models.dim_check_type.base import Base


class CustomCompareMetrics(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_description="",
    ):
        super().__init__(project_id, dataset, table, dim_check_type="custom_compare_metrics", dim_check_description=dim_check_description)

    # def generate_test_sql(self, *, params: Dict[Any, Any]) -> str:
    #     return super().generate_test_sql(params=params)

    # def execute_test_sql(self, sql: str) -> Any:
    #     return super().execute_test_sql(sql=sql)
