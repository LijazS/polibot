import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from polibot.cli import main
from polibot.storage import ParquetArchive, RecordedEnvelope, RecordKind


def test_replay_cli_reports_manifest_and_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    record = RecordedEnvelope(
        record_id=UUID(int=1),
        ordinal=0,
        kind=RecordKind.BOOK_SNAPSHOT,
        market_id="m1",
        source_timestamp=datetime(2026, 9, 4, tzinfo=UTC),
        received_at=datetime(2026, 9, 4, tzinfo=UTC),
        payload_json="{}",
    )
    archive = tmp_path / "events.parquet"
    ParquetArchive().write(archive, (record,))
    result = main(
        [
            "replay",
            str(archive),
            "--market",
            "m1",
            "--strategy-version",
            "test-v1",
            "--config-fingerprint",
            "sha256:test",
            "--latency-model",
            "recorded",
            "--fee-model",
            "recorded",
        ]
    )
    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["processed"] == 1
    assert output["manifest"]["strategy_version"] == "test-v1"
