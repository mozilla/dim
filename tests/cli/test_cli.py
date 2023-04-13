import datetime
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dim.cli import backfill, mute, run, unmute, validate
from dim.error import CmdDateInfoNotProvidedException, DateRangeException, DimConfigError


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
    cmd_args = "--project_id={} --dataset={} --table={}".format(*backfill_settings)
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
    "date,fail_process_on_failure,expected_exit_code,expected_exception",
    [
        ("2022-01-01", True, 0, None),
        ("2022/01/01", False, 2, SystemExit),
        (None, False, 2, SystemExit),
    ],
)
def test_run(
    run_patch,
    runner,
    run_settings,
    date,
    fail_process_on_failure,
    expected_exit_code,
    expected_exception,
):
    cmd_args = "--project_id={} --dataset={} --table={}".format(*run_settings)
    cmd_args += " --fail_process_on_failure" if fail_process_on_failure else ""
    cmd_args += f" --date={date}" if date else ""

    result = runner.invoke(run, cmd_args.split(" "))

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code

    if actual_exit_code == 0:
        run_patch.assert_called_once_with(
            *run_settings,
            datetime.datetime(*map(int, date.split("-"))),
            fail_process_on_failure=fail_process_on_failure,
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
def test_validate(runner, input_config, expected_exit_code, expected_exception):
    result = runner.invoke(validate, [input_config])

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code


@patch("dim.cli.mute_alerts_for_date")
@pytest.mark.parametrize(
    "date,start_date,end_date,expected_exit_code,\
        expected_call_cnt,expected_exception",
    [
        ("2022-01-01", None, None, 0, 1, None),
        (None, None, None, 1, 0, CmdDateInfoNotProvidedException),
        (None, "2022-01-02", "2022-01-01", 1, 0, DateRangeException),
        (None, "2022-01-01", "2022-01-10", 0, 10, None),
    ],
)
def test_mute(
    mute_patch,
    runner,
    run_settings,
    date,
    start_date,
    end_date,
    expected_exit_code,
    expected_call_cnt,
    expected_exception,
):
    cmd_args = "--project_id={} --dataset={} --table={}".format(*run_settings)
    cmd_args += f" --date={date}" if date else ""
    cmd_args += f" --start_date={start_date}" if start_date else ""
    cmd_args += f" --end_date={end_date}" if end_date else ""

    result = runner.invoke(mute, cmd_args.split(" "))

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code
    assert mute_patch.call_count == expected_call_cnt

    if expected_exit_code == 0 and expected_call_cnt > 1:
        mute_patch.call_args_list[0][0] == (
            *run_settings,
            datetime.datetime(*map(int, start_date.split("-"))),
        )
        mute_patch.call_args_list[-1][0] == (
            *run_settings,
            datetime.datetime(*map(int, end_date.split("-"))),
        )

    if expected_exit_code == 0 and expected_call_cnt == 1:
        mute_patch.assert_called_once_with(
            *run_settings, datetime.datetime(*map(int, date.split("-")))
        )


@patch("dim.cli.unmute_alerts_for_date")
@pytest.mark.parametrize(
    "date,start_date,end_date,expected_exit_code,\
        expected_call_cnt,expected_exception",
    [
        ("2022-01-01", None, None, 0, 1, None),
        (None, None, None, 1, 0, CmdDateInfoNotProvidedException),
        (None, "2022-01-02", "2022-01-01", 1, 0, DateRangeException),
        (None, "2022-01-01", "2022-01-10", 0, 10, None),
    ],
)
def test_unmute(
    unmute_patch,
    runner,
    run_settings,
    date,
    start_date,
    end_date,
    expected_exit_code,
    expected_call_cnt,
    expected_exception,
):
    cmd_args = "--project_id={} --dataset={} --table={}".format(*run_settings)
    cmd_args += f" --date={date}" if date else ""
    cmd_args += f" --start_date={start_date}" if start_date else ""
    cmd_args += f" --end_date={end_date}" if end_date else ""

    result = runner.invoke(unmute, cmd_args.split(" "))

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    assert actual_exit_code == expected_exit_code
    assert unmute_patch.call_count == expected_call_cnt

    if expected_exit_code == 0 and expected_call_cnt > 1:
        unmute_patch.call_args_list[0][0] == (
            *run_settings,
            datetime.datetime(*map(int, start_date.split("-"))),
        )
        unmute_patch.call_args_list[-1][0] == (
            *run_settings,
            datetime.datetime(*map(int, end_date.split("-"))),
        )

    if expected_exit_code == 0 and expected_call_cnt == 1:
        unmute_patch.assert_called_once_with(
            *run_settings, datetime.datetime(*map(int, date.split("-")))
        )
