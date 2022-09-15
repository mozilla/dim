from models.tests.base import Base

## TODO: validate config, correct keys + types
class NotNull(Base):
    TEMPLATE_FILE = "not_null" + Base.TEMPLATE_FILE_EXTENSION

    def __init__(self, name, dataset, config):
        super().__init__(name, config)
        self.config["partition"] = "2020-01-13"
        self.config["dataset"] = dataset

    def generate_test_sql(self):
        return super().generate_test_sql(test_type="not_null")

    def execute_test_sql(self, sql):
        return super().execute_test_sql(sql=sql)