import logging
from datetime import timedelta

import click

from dim.app import run_check
from dim.const import INPUT_DATE_FORMAT, LOGGING_LEVEL, SOURCE_PROJECT
from dim.error import (
    CmdDateInfoNotProvidedException,
    DateRangeException,
    DimConfigError,
)
from dim.models.dim_config import DimConfig
from dim.utils import mute_alerts_for_date, read_config

logging.basicConfig(level=LOGGING_LEVEL)


def validate_date_range(start_date, end_date):
    if start_date > end_date:
        raise DateRangeException("Start date must be older than end date.")

    return start_date, end_date


def validate_config(config_path):
    """
    Validates dim config. Ensures it can ve loaded correctly
    and that it fullfils all requirements.
    """

    logging.info("Validating config: %s" % config_path)

    try:
        DimConfig(**read_config(config_path=config_path)["dim_config"])
    except (KeyError, TypeError) as _err:
        raise DimConfigError(_err)

    logging.info("Config appears to be valid: %s" % config_path)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--project_id", required=False, type=str, default=SOURCE_PROJECT)
@click.option("--dataset", required=True, type=str)
@click.option(
    "--table", required=True, type=str
)  # required for now until we add
# support for grabbing all configs in a dataset
@click.option(
    "--date",
    required=True,
    type=click.DateTime(formats=[INPUT_DATE_FORMAT]),
)  # rename date to something shorter,
# required until we add support for full tables
def run(project_id: str, dataset: str, table: str, date: str):
    run_check(project_id, dataset, table, date)


@cli.command()
@click.option("--project_id", required=False, type=str, default=SOURCE_PROJECT)
@click.option("--dataset", required=True, type=str)
@click.option(
    "--table", required=True, type=str
)  # required for now until we add support
# for grabbing all configs in a dataset
@click.option(
    "--start_date",
    required=True,
    type=click.DateTime(formats=[INPUT_DATE_FORMAT]),
)
@click.option(
    "--end_date",
    required=True,
    type=click.DateTime(formats=[INPUT_DATE_FORMAT]),
)
def backfill(
    project_id: str, dataset: str, table: str, start_date: str, end_date: str
):
    """
    Cmd to trigger tests execution for the specified table
    for the specified date range.
    """

    validate_date_range(start_date, end_date)

    logging.info(
        "Running dim backfill checks on %s:%s.%s for date range: %s - %s"
        % (project_id, dataset, table, start_date, end_date)
    )
    date = start_date
    while date <= end_date:
        run_check(project_id, dataset, table, date)
        date += timedelta(days=1)

    logging.info(
        "Dim backfill completed for %s:%s.%s for date range: %s - %s"
        % (project_id, dataset, table, start_date, end_date)
    )


@cli.command()
@click.argument("config_path")
def validate(config_path: str):
    """
    Cmd used to valide a dim yaml config. Ensures the yaml file
    can be loaded correctly and that it fullfils all requirements.
    """

    validate_config(config_path)


@cli.command()
@click.option("--project_id", required=False, type=str, default=SOURCE_PROJECT)
@click.option("--dataset", required=True, type=str)
@click.option(
    "--table", required=True, type=str
)  # required for now until we add support
# for grabbing all configs in a dataset
@click.option(
    "--start_date",
    required=False,
    type=click.DateTime(formats=[INPUT_DATE_FORMAT]),
)
@click.option(
    "--end_date",
    required=False,
    type=click.DateTime(formats=[INPUT_DATE_FORMAT]),
)
@click.option(
    "--date",
    required=False,
    type=click.DateTime(formats=[INPUT_DATE_FORMAT]),
)
def mute(
    project_id: str,
    dataset: str,
    table: str,
    start_date: click.DateTime,
    end_date: click.DateTime,
    date: click.DateTime,
):
    if not start_date and not end_date and not date:
        raise CmdDateInfoNotProvidedException(
            """\
            Need to provide a date range using \
            `--start_date` and `--end_date` or \
            a `--date` for which to mute alerts
            """
        )

    if start_date and end_date:
        logging.info(
            "Muting all alerts for %s:%s.%s for date range: %s - %s"
            % (project_id, dataset, table, start_date, end_date)
        )

    if not start_date and not end_date:
        start_date = end_date = date

    if not any([start_date, end_date]):
        raise CmdDateInfoNotProvidedException(
            """\
            Please make sure both `--start_date` \
            and `--end_date` have a date value provided
            """
        )

    validate_date_range(start_date, end_date)

    date_iteration = start_date
    while date_iteration <= end_date:
        mute_alerts_for_date(project_id, dataset, table, date_iteration)
        date_iteration += timedelta(days=1)
