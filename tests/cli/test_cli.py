import pytest
from unittest.mock import patch

from click.testing import CliRunner
from dim.cli import backfill, run
from dim.error import DateRangeException


# @pytest.fixture
# def runner():
#     return CliRunner()


@patch("dim.cli.run")
@pytest.mark.parametrize(
    "cmd,args,expected_exit_code,expected_exception", [
        (backfill, ["--project=data-monitoring-dev", "--dataset=dummy", "--table=active_users_aggregates_v1", "--start_date=2022-01-01", "--end_date=2022-01-02",], 0, None),
        # (backfill, ["--project=data-monitoring-dev", "--dataset=dummy", "--table=active_users_aggregates_v1", "--start_date=2022-01-02", "--end_date=2022-01-01",], 1, DateRangeException),
        # (backfill, ["--project=data-monitoring-dev", "--dataset=dummy", "--table=active_users_aggregates_v1",], 2, SystemExit),
        # (backfill, ["--project=data-monitoring-dev", "--dataset=dummy", "--table=active_users_aggregates_v1", "--start_date=2022/01/01", "--end_date=2022-01-02",], 2, SystemExit),
        # (backfill, ["--project=data-monitoring-dev", "--dataset=dummy", "--table=active_users_aggregates_v1", "--start_date=2022-01-01", "--end_date=2022/01/02",], 2, SystemExit),
    ]
)
def test_backfill(run_patch, cmd, args, expected_exit_code, expected_exception):
    result = CliRunner().invoke(cmd, args)

    actual_exit_code = result.exit_code

    if actual_exit_code != 0:
        assert result.exc_info[0] == expected_exception

    if actual_exit_code == 0:
        import logging
        run_patch()
        logging.error(run_patch)
        logging.error(dir(run_patch))
        assert run_patch.assert_called()

    assert actual_exit_code == expected_exit_code
