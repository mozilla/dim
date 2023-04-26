from dim.models.dim_check_type.base import Base


class TableRowCount(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_title="",
        dim_check_description="Checking if the row count in the table is as expected.",
    ):
        super().__init__(
            project_id,
            dataset,
            table,
            dim_check_type="table_row_count",
            dim_check_title=dim_check_title,
            dim_check_description=dim_check_description,
        )
