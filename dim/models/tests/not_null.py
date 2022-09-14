from models.tests.base import Base
import jinja2

class NotNull(Base):
    TEMPLATE_FILE = "not_null.sql.jinja"

    def __init__(self, name, dataset, config):
        super().__init__(name, config)
        self.config["partition"] = "2020-01-13"
        self.config["dataset"] = dataset

    ## TODO: validate config, correct keys + types

    def generate_test_sql(self):
        templateLoader = jinja2.FileSystemLoader(searchpath=Base.TEMPLATES_LOC)
        templateEnv = jinja2.Environment(loader=templateLoader)

        template = templateEnv.get_template(NotNull.TEMPLATE_FILE)
        return template.render(self.config)
