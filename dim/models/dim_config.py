from typing import List

import attr


@attr.s(auto_attribs=True)
class DimCheckOptions:
    threshold: str = attr.ib()
    enable_slack_alert: bool = attr.ib()


@attr.s(auto_attribs=True)
class DimCheck:
    type: str = attr.ib()
    options: DimCheckOptions = attr.ib()

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
    dim_tests: List[DimCheck] = attr.ib()

    @owner.validator
    def validate_owner(self, attribute, value):
        """Check that owner is a valid email address."""

        pass

    @tier.validator
    def validate_tier(self, attribute, value):
        """Check that owner is a valid email address."""

        pass
