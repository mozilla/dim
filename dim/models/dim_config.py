from typing import List

import attr


@attr.s(auto_attribs=True)
class DimCheckOptions:
    threshold: str
    slack_alert: bool


@attr.s(auto_attribs=True)
class DimCheck:
    type: str = attr.ib()
    options: DimCheckOptions


@attr.s(auto_attribs=True)
class DimConfig:
    """
    TODO: update the doc string
    """

    owner: str = attr.ib()
    tier: str = attr.ib()
    dim_tests: List[DimCheck] = attr.ib()

    @owner.validator
    def validate_owner(self, attribute, value):
        """Check that owner is a valid email address."""

        pass
