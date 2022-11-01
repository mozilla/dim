from dim.models.dq_checks.base import Base


class TableRowCount(Base):
    TEMPLATE_FILE = "table_row_count" + Base.TEMPLATE_FILE_EXTENSION

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
        self.config["dq_check"] = "table_row_count"
        self.config["partition"] = date_partition_parameter
        self.name = dataset + "__" + "table_row_count"

    def generate_test_sql(self):
        return super().generate_test_sql(dq_check="table_row_count")

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)
