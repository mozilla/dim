from models.tests.base import Base

## TODO: validate config, correct keys + types
class NotNull(Base):
    TEMPLATE_FILE = "not_null" + Base.TEMPLATE_FILE_EXTENSION

    def __init__(self, project_id, dataset_id, table_id, config):
        super().__init__(config)
        self.config["partition"] = "2020-01-13"
        self.config["project_id"] = project_id
        self.config["dataset_id"] = dataset_id
        self.config["table_id"] = table_id
        self.config["dq_check"] = "not_null"
        self.name = dataset_id + '__' + "not_null"

    def generate_test_sql(self):
        return super().generate_test_sql(dq_check="not_null")

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)