from dim.models.dim_check_type.base import Base


class ColumnSumNotZero(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_title=None,
        dim_check_description=None,
    ):
        super().__init__(
            project_id,
            dataset,
            table,
            dim_check_type="column_sum_not_zero",
            dim_check_title=dim_check_title,
            dim_check_description=dim_check_description,
        )
