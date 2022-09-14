
class Base:
    TEMPLATES_LOC = "dim/models/tests/templates"

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def generate_test_sql(self):
        raise NotImplementedError