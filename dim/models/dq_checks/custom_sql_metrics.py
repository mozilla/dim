from dim.models.dq_checks.base import Base


## TODO: validate config, correct keys + types
class CustomSqlMetrics(Base):
    TEMPLATE_FILE = "custom_sql_metrics" + Base.TEMPLATE_FILE_EXTENSION

    def __init__(
        self, project, dataset, table, dataset_owner, date_partition_parameter, config
    ):
        super().__init__(config)
        self.config["partition"] = date_partition_parameter
        self.config["project"] = project
        self.config["dataset"] = dataset
        self.config["table"] = table
        self.config["dq_check"] = "custom_sql_metric"
        self.config["dataset_owner"] = dataset_owner
        self.name = dataset + "__" + "custom_sql_metric"

    def generate_test_sql(self):
        return super().generate_test_sql(dq_check="custom_sql")

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)
