import datetime
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dim.cli import backfill, run, validate
from dim.error import DateRangeException, DimConfigError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def backfill_settings():
    return (
        "data-monitoring-dev",
        "dummy",
        "active_users_aggregates_v1",
    )


@patch("dim.cli.run_check")
@pytest.mark.parametrize(
    "start,end,expected_call_cnt, expected_exit_code,expected_exception",
    [
        ("2022-01-01", "2022-01-02", 2, 0, None),
        ("2022-01-01", "2022-01-20", 20, 0, None),
        ("2022-01-02", "2022-01-01", 0, 1, DateRangeException),
        ("2022/01/01", "2022-01-02", 0, 2, SystemExit),
        ("2022-01-01", "2022/01/02", 0, 2, SystemExit),
        (None, "2022/01/02", 0, 2, SystemExit),
        ("2022-01-01", None, 0, 2, SystemExit),
        (None, None, 0, 2, SystemExit),
    ],
)
def test_backfill(
    run_patch,
    runner,
    backfill_settings,
    start,
    end,
    expected_call_cnt,
    expected_exit_code,
    expected_exception,
):
    cmd_args = "--project={} --dataset={} --table={}".format(
        *backfill_settings
    )
    cmd_args += f" --start_date={start}" if start else ""
    cmd_args += f" --end_date={end}" if end else ""

    result = runner.invoke(backfill, cmd_args.split(" "))

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code

    assert run_patch.call_count == expected_call_cnt

    if actual_exit_code == 0:
        run_patch.call_args_list[0][0] == (
            *backfill_settings,
            datetime.datetime(*map(int, start.split("-"))),
        )
        run_patch.call_args_list[-1][0] == (
            *backfill_settings,
            datetime.datetime(*map(int, end.split("-"))),
        )


@pytest.fixture
def run_settings():
    return (
        "data-monitoring-dev",
        "dummy",
        "active_users_aggregates_v1",
    )


@patch("dim.cli.run_check")
@pytest.mark.parametrize(
    "date,expected_exit_code,expected_exception",
    [
        ("2022-01-01", 0, None),
        ("2022/01/01", 2, SystemExit),
        (None, 2, SystemExit),
    ],
)
def test_run(
    run_patch,
    runner,
    run_settings,
    date,
    expected_exit_code,
    expected_exception,
):
    cmd_args = "--project={} --dataset={} --table={}".format(*run_settings)
    cmd_args += f" --date_partition_parameter={date}" if date else ""

    result = runner.invoke(run, cmd_args.split(" "))

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code

    if actual_exit_code == 0:
        run_patch.assert_called_once_with(
            *run_settings, datetime.datetime(*map(int, date.split("-")))
        )


@pytest.mark.parametrize(
    "input_config,expected_exit_code,expected_exception",
    [
        ("tests/cli/test_configs/valid.yaml", 0, None),
        (
            "tests/cli/test_configs/missing_dim_config_key.yaml",
            1,
            DimConfigError,
        ),
        ("tests/cli/test_configs/missing_tier.yaml", 1, DimConfigError),
    ],
)
def test_validate(
    runner, input_config, expected_exit_code, expected_exception
):
    result = runner.invoke(validate, [input_config])

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code
