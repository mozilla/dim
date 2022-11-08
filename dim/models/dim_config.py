from datetime import datetime
from typing import List, Optional

import attr
import cattrs

from dim.const import VALID_TIERS


@attr.s(auto_attribs=True)
class SlackEntities:
    """ """

    channels: List[str] = attr.ib()
    # users: List[str] = attr.ib()


@attr.s(auto_attribs=True)
class SlackAlertConfig:
    """ """

    enabled: bool = attr.ib()
    notify: SlackEntities = attr.ib()


@attr.s(auto_attribs=True)
class Owner:
    """ """

    email: str
    slack: Optional[str] = attr.ib(default=None)

    # @email.validator
    # def validate_email(self, attribute, value):
    #     """Check that owner is a valid email address."""

    #     pass


@attr.s(auto_attribs=True)
class DimCheckParams:
    """ """

    condition: Optional[str] = attr.ib(None)
    sql: Optional[str] = attr.ib(None)
    expected_values: Optional[List[str]] = attr.ib(None)
    columns: Optional[List[str]] = attr.ib(None)
    partition: Optional[datetime] = attr.ib(None)
    enable_alerts_enabled: Optional[bool] = attr.ib(False)


@attr.s(auto_attribs=True)
class DimCheck:
    """ """

    type: str = attr.ib()
    params: DimCheckParams

    @type.validator
    def validate_type(self, attribute, value):
        """Check that owner is a valid DimCheck type is specified."""

        pass


@attr.s(auto_attribs=True)
class DimConfig:
    """
    TODO: update the doc string
    """

    owner: Owner = attr.ib()
    tier: str = attr.ib()
    dim_tests: List[DimCheck]
    slack_alerts: Optional[SlackAlertConfig] = attr.ib(
        default=SlackAlertConfig(
            enabled=False,
            notify=SlackEntities(
                channels=list(),
            ),
        )
    )

    @tier.validator
    def validate_tier(self, attribute, value):
        """Check that tier provided is valid."""

        if value not in VALID_TIERS:
            msg = f"Invalid tier provided: {value}. \
                Valid options include: {VALID_TIERS}"
            raise AttributeError(msg)

        return

    @classmethod
    def from_dict(cls, d):
        """
        Converts the DimConfig object to a dictionary structure.
        """

        converter = cattrs.BaseConverter()
        return converter.structure(d, cls)
