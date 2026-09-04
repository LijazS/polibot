from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class HealthReport:
    healthy: bool
    checked_at: datetime
    failures: tuple[str, ...]


class HealthService:
    def __init__(self, checks: dict[str, Callable[[], bool]] | None = None) -> None:
        self._checks = checks or {}

    def check(self) -> HealthReport:
        failures = tuple(name for name, check in self._checks.items() if not check())
        return HealthReport(not failures, datetime.now(UTC), failures)
