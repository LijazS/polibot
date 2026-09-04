import pytest
from pydantic import ValidationError

from polibot.config import ExecutionMode, Settings


def test_default_mode_is_not_live() -> None:
    settings = Settings(_env_file=None)
    assert settings.execution_mode is ExecutionMode.PAPER
    assert settings.live_trading_enabled is False


def test_live_mode_fails_closed_without_separate_enablement() -> None:
    with pytest.raises(ValidationError, match="LIVE mode requires"):
        Settings(execution_mode=ExecutionMode.LIVE, _env_file=None)

