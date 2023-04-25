from dim.models.dim_check_type.base import Base


class ColumnLength(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_title="",
        dim_check_description="Checking that the number of characters matches our expectations.",
    ):
        super().__init__(project_id, dataset, table, dim_check_type="column_length", dim_check_title=dim_check_title, dim_check_description=dim_check_description)
