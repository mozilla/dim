from dim.models.tests.base import Base

## TODO: validate config, correct keys + types
class CustomSqlMetrics(Base):
    TEMPLATE_FILE = "custom_sql_metrics" + Base.TEMPLATE_FILE_EXTENSION

    def __init__(self, project_id, dataset_id, table_id, dataset_owner, config):
        super().__init__(config)
        self.config["partition"] = "2020-01-13"
        self.config["project_id"] = project_id
        self.config["dataset_id"] = dataset_id
        self.config["table_id"] = table_id
        self.config["dq_check"] = "custom_sql_metric"
        self.config[dataset_owner] = dataset_owner
        self.name = dataset_id + '__' + "custom_sql_metric"

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)