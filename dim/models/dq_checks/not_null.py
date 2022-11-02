from dim.models.dq_checks.base import Base


class NotNull(Base):
    DQ_CHECK_NAME = "not_null"

    def __init__(
        self,
        project_id,
        dataset,
        table,
        dataset_owner,
        date,
        config,
    ):
        super().__init__(project_id, dataset, table, dataset_owner)
        self.config = config
        self.config.partition = date

    def generate_test_sql(self):
        return super().generate_test_sql(dq_check=self.DQ_CHECK_NAME)

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)
