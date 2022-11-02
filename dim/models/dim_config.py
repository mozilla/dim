from datetime import datetime
from typing import List, Optional

import attr
import cattrs


@attr.s(auto_attribs=True)
class DimCheckOptions:
    threshold: Optional[str] = attr.ib()
    columns: Optional[List[str]] = attr.ib()
    partition: Optional[datetime] = attr.ib(None)
    enable_slack_alert: Optional[bool] = attr.ib(False)


@attr.s(auto_attribs=True)
class DimCheck:
    type: str = attr.ib()
    options: DimCheckOptions

    @type.validator
    def validate_type(self, attribute, value):
        """Check that owner is a valid email address."""

        pass


@attr.s(auto_attribs=True)
class DimConfig:
    """
    TODO: update the doc string
    """

    owner: str = attr.ib()
    tier: str = attr.ib()
    dim_tests: List[DimCheck]

    @owner.validator
    def validate_owner(self, attribute, value):
        """Check that owner is a valid email address."""

        pass

    @tier.validator
    def validate_tier(self, attribute, value):
        """Check that owner is a valid email address."""

        pass

    @classmethod
    def from_dict(cls, d):
        converter = cattrs.BaseConverter()
        return converter.structure(d, cls)
