from typing import Any, Dict

from dim.models.dim_check_type.base import Base


class MatchesRegex(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_title="",
        dim_check_description="",
    ):
        super().__init__(project_id, dataset, table, dim_check_type="matches_regex", dim_check_title=dim_check_title, dim_check_description=dim_check_description)
