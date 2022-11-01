from dim.models.dq_checks.base import Base


class NotNull(Base):
    TEMPLATE_FILE = "not_null" + Base.TEMPLATE_FILE_EXTENSION

    def __init__(
        self,
        project,
        dataset,
        table,
        date_partition_parameter,
        config,
    ):
        super().__init__(config)
        self.config["project"] = project
        self.config["dataset"] = dataset
        self.config["table"] = table
        self.config["dq_check"] = "not_null"
        self.config["partition"] = date_partition_parameter
        self.name = dataset + "__" + "not_null"

    def generate_test_sql(self):
        return super().generate_test_sql(dq_check="not_null")

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)
