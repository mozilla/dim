from dim.models.dim_check_type.base import Base


class NotNull(Base):
    dim_check_type_NAME = "not_null"

    def __init__(
        self,
        project_id,
        dataset,
        table,
    ):
        super().__init__(project_id, dataset, table, self.dim_check_type_NAME)

    def generate_test_sql(self, params):
        return super().generate_test_sql(params=params)

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)
