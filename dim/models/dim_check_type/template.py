from typing import Any, Dict

from dim.models.dim_check_type.base import Base


class REPLACE_ME(Base):
    def __init__(
        self,
        project_id,
        dataset,
        table,
        dim_check_title="",
        dim_check_description="",
    ):
        super().__init__(project_id, dataset, table, dim_check_type="REPLACE_ME_WITH_CHECK_TYPE_NAME", dim_check_title=dim_check_title, dim_check_description=dim_check_description)
