from dim.models.dq_checks.base import Base


class ValueInSet(Base):
    DQ_CHECK_NAME = "value_in_set"

    def __init__(
        self,
        project_id,
        dataset,
        table,
    ):
        super().__init__(project_id, dataset, table, self.DQ_CHECK_NAME)

    def generate_test_sql(self, params):
        return super().generate_test_sql(params=params)

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)
