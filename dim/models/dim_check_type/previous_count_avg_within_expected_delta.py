from dim.models.dim_check_type.base import Base


class PreviousCountAvgWithinExpectedDelta(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_title="",
        dim_check_description="",
    ):
        super().__init__(
            project_id,
            dataset,
            table,
            dim_check_type="previous_count_avg_within_expected_delta",
            dim_check_title=dim_check_title,
            dim_check_description=dim_check_description,
        )
